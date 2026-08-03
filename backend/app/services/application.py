from __future__ import annotations

from collections.abc import Awaitable, Sequence
from dataclasses import dataclass
from uuid import UUID

from pydantic import JsonValue
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import (
    Artifact,
    DelayedEffect,
    Event,
    FutureSelfConversation,
    FutureSelfMessage,
    LifeStateSnapshot,
    PersonProfile,
    Scenario,
    Universe,
)
from app.models.enums import (
    EventImportance,
    EventSource,
    EventStatus,
    MessageRole,
    UniverseStatus,
)
from app.repositories import (
    ArtifactRepository,
    ChoiceRepository,
    EventRepository,
    FutureSelfConversationRepository,
    FutureSelfMessageRepository,
    LifeStateSnapshotRepository,
    PersonProfileRepository,
    ScenarioRepository,
    UniverseRepository,
)
from app.schemas.api import (
    AdvancementResponse,
    ComparisonHistoryPoint,
    ComparisonStats,
    EventDetailResponse,
    FinancialPosition,
    FutureSelfConversationResponse,
    Pagination,
    ScenarioComparisonResponse,
    ScenarioDetailResponse,
    ScoreComponents,
    UniverseComparison,
    UniverseGenerationResponse,
    UniverseResetResponse,
    UniverseStateResponse,
)
from app.schemas.domain import (
    ArtifactRead,
    ChoiceRead,
    EventRead,
    FutureSelfConversationRead,
    FutureSelfMessageRead,
    LifeStateSnapshotRead,
    PersonProfileCreate,
    PersonProfileRead,
    PersonProfileUpdate,
    ScenarioCreate,
    ScenarioRead,
    UniverseRead,
)
from app.services.narrative import (
    FutureSelfMessage as NarrativeMessage,
)
from app.services.narrative import (
    FutureSelfReplyRequest,
    GeneratedChoice,
    GeneratedEvent,
    GeneratedFutureSelfProfile,
    GeneratedYearSummary,
    MockNarrativeProvider,
    NarrativeContext,
    NarrativeContextBuilder,
    NarrativeProvider,
    ProfileNarrativeSummary,
    UniverseBranchRequest,
)
from app.services.simulation import (
    ChoiceResolutionError,
    SimulationError,
    SimulationService,
    UniverseBlockedError,
    derive_seed,
)
from app.services.simulation.events import ChoiceDefinition, SystemEventDefinition
from app.services.simulation.schemas import ChoiceRequirements, DelayedEffectSpec, EffectPayload

MAX_JSON_SAFE_INTEGER = 2**53 - 1
DEFAULT_MOCK_BRANCH_DIRECTIONS = {
    "Applied AI Leader",
    "Robotics Researcher",
    "Startup Founder",
}
BRANCH_DIRECTIONS_PREFIX = "Optional branch directions:"
LEGACY_MOCK_EVENT_PREFIXES = ("industry-", "research-", "startup-")
CUSTOM_PATH_FLAGS = {"career_path", "education_path", "creator_path", "independent_path"}


class ApplicationServiceError(RuntimeError):
    code = "application_error"

    def __init__(self, message: str, *, details: dict[str, JsonValue] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ResourceNotFoundError(ApplicationServiceError):
    code = "not_found"


class ResourceConflictError(ApplicationServiceError):
    code = "conflict"


class InvalidOperationError(ApplicationServiceError):
    code = "invalid_operation"


class NarrativeUnavailableError(ApplicationServiceError):
    code = "narrative_unavailable"


@dataclass(frozen=True)
class PageResult[T]:
    items: list[T]
    pagination: Pagination


def _pagination(offset: int, limit: int, total: int) -> Pagination:
    return Pagination(
        offset=offset,
        limit=limit,
        total=total,
        has_more=offset + limit < total,
    )


def _required[T](value: T | None, resource: str, resource_id: UUID) -> T:
    if value is None:
        raise ResourceNotFoundError(f"{resource} was not found", details={"id": str(resource_id)})
    return value


class CoreApplicationService:
    """Transaction-owning use cases exposed by the versioned API."""

    def __init__(
        self,
        session: Session,
        narrative_provider: NarrativeProvider | None = None,
    ) -> None:
        self.session = session
        self.provider = narrative_provider or MockNarrativeProvider()
        self.context_builder = NarrativeContextBuilder()
        self.profiles = PersonProfileRepository(session)
        self.scenarios = ScenarioRepository(session)
        self.universes = UniverseRepository(session)
        self.snapshots = LifeStateSnapshotRepository(session)
        self.events = EventRepository(session)
        self.choices = ChoiceRepository(session)
        self.artifacts = ArtifactRepository(session)
        self.conversations = FutureSelfConversationRepository(session)
        self.messages = FutureSelfMessageRepository(session)
        self.simulation = SimulationService(session)

    def list_profiles(self, offset: int, limit: int) -> PageResult[PersonProfileRead]:
        statement = select(PersonProfile).order_by(PersonProfile.created_at, PersonProfile.id)
        rows = list(self.session.scalars(statement.offset(offset).limit(limit)).all())
        total = self.session.scalar(select(func.count()).select_from(PersonProfile)) or 0
        return PageResult(
            [PersonProfileRead.model_validate(row) for row in rows],
            _pagination(offset, limit, total),
        )

    def create_profile(self, payload: PersonProfileCreate) -> PersonProfileRead:
        with self.session.begin():
            profile = self.profiles.add(PersonProfile(**payload.model_dump()))
            return PersonProfileRead.model_validate(profile)

    def get_profile(self, profile_id: UUID) -> PersonProfileRead:
        profile = _required(self.profiles.get(profile_id), "Profile", profile_id)
        return PersonProfileRead.model_validate(profile)

    def update_profile(self, profile_id: UUID, payload: PersonProfileUpdate) -> PersonProfileRead:
        with self.session.begin():
            profile = _required(self.profiles.get(profile_id), "Profile", profile_id)
            changes = payload.model_dump(exclude_unset=True)
            current = PersonProfileRead.model_validate(profile).model_dump(
                exclude={"id", "created_at", "updated_at"}
            )
            validated = PersonProfileCreate.model_validate({**current, **changes})
            updated = self.profiles.update(profile, validated.model_dump())
            return PersonProfileRead.model_validate(updated)

    def delete_profile(self, profile_id: UUID) -> None:
        with self.session.begin():
            profile = _required(self.profiles.get(profile_id), "Profile", profile_id)
            self.profiles.delete(profile)

    def list_scenarios(
        self, offset: int, limit: int, profile_id: UUID | None = None
    ) -> PageResult[ScenarioRead]:
        statement = select(Scenario)
        count_statement = select(func.count()).select_from(Scenario)
        if profile_id is not None:
            statement = statement.where(Scenario.profile_id == profile_id)
            count_statement = count_statement.where(Scenario.profile_id == profile_id)
        statement = statement.order_by(Scenario.created_at, Scenario.id)
        rows = list(self.session.scalars(statement.offset(offset).limit(limit)).all())
        total = self.session.scalar(count_statement) or 0
        return PageResult(
            [ScenarioRead.model_validate(row) for row in rows],
            _pagination(offset, limit, total),
        )

    def create_scenario(self, payload: ScenarioCreate) -> ScenarioRead:
        with self.session.begin():
            _required(self.profiles.get(payload.profile_id), "Profile", payload.profile_id)
            scenario = self.scenarios.add(Scenario(**payload.model_dump()))
            return ScenarioRead.model_validate(scenario)

    def get_scenario(self, scenario_id: UUID) -> ScenarioDetailResponse:
        scenario = _required(self.scenarios.get(scenario_id), "Scenario", scenario_id)
        universes = self.universes.for_scenario(scenario_id)
        return ScenarioDetailResponse(
            scenario=ScenarioRead.model_validate(scenario),
            universes=[UniverseRead.model_validate(universe) for universe in universes],
        )

    async def generate_universes(self, scenario_id: UUID) -> UniverseGenerationResponse:
        with self.session.begin():
            scenario = _required(self.scenarios.get(scenario_id), "Scenario", scenario_id)
            branch_directions = self._branch_directions(scenario)
            existing = self.universes.for_scenario(scenario_id)
            if existing:
                if len(existing) != scenario.number_of_universes:
                    raise ResourceConflictError(
                        "Scenario has a partial universe set and cannot be regenerated safely",
                        details={
                            "existing": len(existing),
                            "expected": scenario.number_of_universes,
                        },
                    )
                if self._can_replace_non_llm_branches(existing) or self._can_repair_legacy_branches(
                    existing, branch_directions
                ):
                    for universe in existing:
                        self.universes.delete(universe)
                    self.session.flush()
                else:
                    await self._refresh_pending_non_llm_events(existing)
                    return UniverseGenerationResponse(
                        generated=False,
                        universes=[UniverseRead.model_validate(universe) for universe in existing],
                    )

            profile = _required(
                self.profiles.get(scenario.profile_id), "Profile", scenario.profile_id
            )
            request = UniverseBranchRequest(
                profile=self._profile_summary(profile),
                decision_question=scenario.decision_question,
                scenario_seed=scenario.seed,
                simulation_mode=scenario.simulation_mode,
                number_of_branches=scenario.number_of_universes,
                branch_directions=branch_directions,
            )
            branches = await self._narrative(self.provider.generate_universe_branches(request))
            if len(branches) != scenario.number_of_universes:
                raise NarrativeUnavailableError(
                    "Narrative provider returned the wrong number of universe branches"
                )

            created: list[Universe] = []
            for index, branch in enumerate(branches):
                # Universe seeds cross the JSON boundary even though only the
                # backend uses them. Keep new values exact in JavaScript clients.
                seed = derive_seed(scenario.seed, branch.slug, index) % MAX_JSON_SAFE_INTEGER
                state = branch.proposed_initial_state
                universe = self.universes.add(
                    Universe(
                        scenario_id=scenario.id,
                        name=branch.name,
                        slug=branch.slug,
                        subtitle=branch.subtitle,
                        premise=branch.premise,
                        visual_theme={
                            "accent": branch.accent_color,
                            "motif": branch.visual_theme,
                            "narrative_provider": self._last_narrative_provider_name(),
                        },
                        starting_direction=branch.starting_direction,
                        current_year=profile.starting_year,
                        current_age=profile.starting_age,
                        random_seed=seed,
                        status=UniverseStatus.ACTIVE,
                    )
                )
                self.snapshots.add(
                    LifeStateSnapshot(
                        universe_id=universe.id,
                        year=profile.starting_year,
                        age=profile.starting_age,
                        location=state.location,
                        career_title=state.career_title,
                        career_level=state.career_level,
                        monthly_income_eur=state.monthly_income_eur,
                        net_worth_eur=state.net_worth_eur,
                        health=state.health,
                        relationships=state.relationships,
                        research_impact=state.research_impact,
                        reputation=state.reputation,
                        freedom=state.freedom,
                        stress=state.stress,
                        happiness=state.happiness,
                        discipline=state.discipline,
                        creativity=state.creativity,
                        chaos=state.chaos,
                        skills=state.skills,
                        active_flags=state.active_flags,
                    )
                )
                created.append(universe)
            return UniverseGenerationResponse(
                generated=True,
                universes=[UniverseRead.model_validate(universe) for universe in created],
            )

    @staticmethod
    def _branch_directions(scenario: Scenario) -> list[str]:
        for line in scenario.description.splitlines():
            stripped = line.strip()
            if not stripped.startswith(BRANCH_DIRECTIONS_PREFIX):
                continue
            encoded = stripped.removeprefix(BRANCH_DIRECTIONS_PREFIX).strip()
            if encoded.endswith("."):
                encoded = encoded[:-1]
            directions = [item.strip() for item in encoded.split("|") if item.strip()]
            if len(directions) == scenario.number_of_universes:
                return directions
        return []

    def _can_repair_legacy_branches(
        self, existing: list[Universe], branch_directions: list[str]
    ) -> bool:
        if not branch_directions:
            return False
        current_directions = {universe.starting_direction for universe in existing}
        if current_directions != DEFAULT_MOCK_BRANCH_DIRECTIONS:
            return False
        if current_directions == set(branch_directions):
            return False
        return all(
            len(self.snapshots.for_universe(universe.id)) == 1
            and not self.events.for_universe(universe.id)
            and not self.artifacts.for_universe(universe.id)
            and not self.conversations.for_universe(universe.id)
            for universe in existing
        )

    def _can_replace_non_llm_branches(self, universes: list[Universe]) -> bool:
        if not self.provider.llm_only:
            return False
        if all(
            universe.visual_theme.get("narrative_provider") == "openai" for universe in universes
        ):
            return False
        for universe in universes:
            if len(self.snapshots.for_universe(universe.id)) != 1:
                return False
            events = self.events.for_universe(universe.id)
            if any(
                event.status != EventStatus.PENDING
                or any(choice.selected for choice in self.choices.for_event(event.id))
                for event in events
            ):
                return False
            if self.artifacts.for_universe(universe.id) or self.conversations.for_universe(
                universe.id
            ):
                return False
            delayed_count = self.session.scalar(
                select(func.count())
                .select_from(DelayedEffect)
                .where(DelayedEffect.universe_id == universe.id)
            )
            if delayed_count:
                return False
        return True

    async def _refresh_pending_non_llm_events(self, universes: list[Universe]) -> None:
        for universe in universes:
            pending = self.events.for_universe(universe.id, status=EventStatus.PENDING)
            if len(pending) != 1:
                continue
            event = pending[0]
            if any(choice.selected for choice in self.choices.for_event(event.id)):
                continue
            latest = _required(self.snapshots.latest(universe.id), "Universe state", universe.id)
            is_legacy_custom_event = (
                event.source == EventSource.MOCK
                and event.narrative_key is not None
                and event.narrative_key.startswith(LEGACY_MOCK_EVENT_PREFIXES)
                and bool(CUSTOM_PATH_FLAGS.intersection(latest.active_flags))
            )
            is_non_llm_event_in_strict_mode = (
                self.provider.llm_only and event.source != EventSource.OPENAI
            )
            if not is_legacy_custom_event and not is_non_llm_event_in_strict_mode:
                continue

            self.events.delete(event)
            self.session.flush()
            universe.status = UniverseStatus.ACTIVE
            previous = self.events.for_universe(universe.id)
            context = self._context(universe, latest, previous)
            generated = await self._narrative(self.provider.generate_significant_event(context))
            result = self.simulation.advance_universe_in_transaction(
                universe.id, self._event_definition(generated)
            )
            if not result.blocked or result.event_id is None:
                raise InvalidOperationError("Legacy event repair must produce a pending decision")
            replacement = _required(self.events.get(result.event_id), "Event", result.event_id)
            replacement.is_generated = True
            replacement.source = self._provider_event_source()

    def get_universe(self, universe_id: UUID) -> UniverseRead:
        universe = _required(self.universes.get(universe_id), "Universe", universe_id)
        return UniverseRead.model_validate(universe)

    def get_universe_state(self, universe_id: UUID) -> UniverseStateResponse:
        universe = _required(self.universes.get(universe_id), "Universe", universe_id)
        state = _required(self.snapshots.latest(universe_id), "Universe state", universe_id)
        return UniverseStateResponse(
            universe=UniverseRead.model_validate(universe),
            state=LifeStateSnapshotRead.model_validate(state),
        )

    def get_timeline(
        self, universe_id: UUID, offset: int, limit: int
    ) -> PageResult[LifeStateSnapshotRead]:
        _required(self.universes.get(universe_id), "Universe", universe_id)
        condition = LifeStateSnapshot.universe_id == universe_id
        statement = (
            select(LifeStateSnapshot)
            .where(condition)
            .order_by(LifeStateSnapshot.year, LifeStateSnapshot.created_at)
        )
        rows = list(self.session.scalars(statement.offset(offset).limit(limit)).all())
        total = (
            self.session.scalar(
                select(func.count()).select_from(LifeStateSnapshot).where(condition)
            )
            or 0
        )
        return PageResult(
            [LifeStateSnapshotRead.model_validate(row) for row in rows],
            _pagination(offset, limit, total),
        )

    async def advance_universe(self, universe_id: UUID) -> AdvancementResponse:
        try:
            with self.session.begin():
                universe = _required(self.universes.get(universe_id), "Universe", universe_id)
                latest = _required(
                    self.snapshots.latest(universe_id), "Universe state", universe_id
                )
                previous = self.events.for_universe(universe_id)
                context = self._context(universe, latest, previous)
                generated = await self._narrative(self.provider.generate_significant_event(context))
                definition = self._event_definition(generated)
                result = self.simulation.advance_universe_in_transaction(universe_id, definition)
                if result.event_id is None:
                    raise InvalidOperationError("Advancement did not persist an event")
                persisted = _required(self.events.get(result.event_id), "Event", result.event_id)
                persisted.is_generated = True
                persisted.source = self._provider_event_source()
                if result.blocked:
                    return self._advancement_response(result, persisted)
                return await self._complete_advancement(result, universe, persisted, generated)
        except UniverseBlockedError as error:
            raise ResourceConflictError(
                str(error), details={"universe_id": str(universe_id)}
            ) from error
        except SimulationError as error:
            raise InvalidOperationError(str(error)) from error

    async def select_choice(self, event_id: UUID, choice_id: UUID) -> AdvancementResponse:
        try:
            with self.session.begin():
                event = self.events.get(event_id)
                choice = self.choices.get(choice_id)
                if event is None or choice is None or choice.event_id != event_id:
                    raise ResourceNotFoundError(
                        "Choice was not found for this event",
                        details={"event_id": str(event_id), "choice_id": str(choice_id)},
                    )
                universe = _required(
                    self.universes.get(event.universe_id), "Universe", event.universe_id
                )
                if choice.selected:
                    result = self.simulation.resolve_choice_in_transaction(event_id, choice_id)
                    return self._advancement_response(result, event)
                if event.status == EventStatus.RESOLVED:
                    raise ResourceConflictError(
                        "Event was already resolved with a different choice"
                    )

                generated = self._stored_generated_event(event)
                result = self.simulation.resolve_choice_in_transaction(
                    event_id, choice_id, self._event_definition(generated)
                )
                return await self._complete_advancement(result, universe, event, generated)
        except ChoiceResolutionError as error:
            raise ResourceConflictError(str(error)) from error
        except SimulationError as error:
            raise InvalidOperationError(str(error)) from error

    def get_events(self, universe_id: UUID, offset: int, limit: int) -> PageResult[EventRead]:
        _required(self.universes.get(universe_id), "Universe", universe_id)
        condition = Event.universe_id == universe_id
        statement = select(Event).where(condition).order_by(Event.year, Event.created_at)
        rows = list(self.session.scalars(statement.offset(offset).limit(limit)).all())
        total = self.session.scalar(select(func.count()).select_from(Event).where(condition)) or 0
        return PageResult(
            [EventRead.model_validate(row) for row in rows],
            _pagination(offset, limit, total),
        )

    def get_event(self, event_id: UUID) -> EventDetailResponse:
        event = _required(self.events.get(event_id), "Event", event_id)
        return self._event_response(event)

    def get_artifacts(self, universe_id: UUID, offset: int, limit: int) -> PageResult[ArtifactRead]:
        _required(self.universes.get(universe_id), "Universe", universe_id)
        condition = Artifact.universe_id == universe_id
        statement = select(Artifact).where(condition).order_by(Artifact.year, Artifact.created_at)
        rows = list(self.session.scalars(statement.offset(offset).limit(limit)).all())
        total = (
            self.session.scalar(select(func.count()).select_from(Artifact).where(condition)) or 0
        )
        return PageResult(
            [ArtifactRead.model_validate(row) for row in rows],
            _pagination(offset, limit, total),
        )

    def get_artifact(self, artifact_id: UUID) -> ArtifactRead:
        artifact = _required(self.artifacts.get(artifact_id), "Artifact", artifact_id)
        return ArtifactRead.model_validate(artifact)

    def reset_universe(self, universe_id: UUID) -> UniverseResetResponse:
        with self.session.begin():
            universe = _required(self.universes.get(universe_id), "Universe", universe_id)
            initial = self.session.scalar(
                select(LifeStateSnapshot)
                .where(LifeStateSnapshot.universe_id == universe_id)
                .order_by(LifeStateSnapshot.year, LifeStateSnapshot.created_at)
                .limit(1)
            )
            initial = _required(initial, "Universe state", universe_id)
            self.session.execute(delete(Artifact).where(Artifact.universe_id == universe_id))
            self.session.execute(
                delete(FutureSelfConversation).where(
                    FutureSelfConversation.universe_id == universe_id
                )
            )
            self.session.execute(
                delete(DelayedEffect).where(DelayedEffect.universe_id == universe_id)
            )
            self.session.execute(delete(Event).where(Event.universe_id == universe_id))
            self.session.execute(
                delete(LifeStateSnapshot).where(
                    LifeStateSnapshot.universe_id == universe_id,
                    LifeStateSnapshot.id != initial.id,
                )
            )
            universe.current_year = initial.year
            universe.current_age = initial.age
            universe.status = UniverseStatus.ACTIVE
            self.session.flush()
            return UniverseResetResponse(
                universe=UniverseRead.model_validate(universe),
                state=LifeStateSnapshotRead.model_validate(initial),
            )

    def compare_universes(self, scenario_id: UUID) -> ScenarioComparisonResponse:
        scenario = _required(self.scenarios.get(scenario_id), "Scenario", scenario_id)
        comparisons: list[UniverseComparison] = []
        for universe in self.universes.for_scenario(scenario_id):
            states = self.snapshots.for_universe(universe.id)
            if not states:
                continue
            events = self.events.for_universe(universe.id)
            latest = states[-1]
            decisions: list[str] = []
            regrets: list[str] = []
            for event in events:
                selected = next((choice for choice in event.choices if choice.selected), None)
                if selected is None:
                    continue
                decisions.append(f"{event.year}: {selected.label}")
                stats = selected.immediate_effects.get("stats", {})
                if isinstance(stats, dict) and (
                    any(stats.get(name, 0) < 0 for name in ("health", "happiness", "relationships"))
                    or stats.get("stress", 0) > 0
                ):
                    regrets.append(f"{selected.label} during {event.title}")
            achievements = [
                event.title
                for event in events
                if event.status == EventStatus.RESOLVED
                and event.importance in {EventImportance.NOTABLE, EventImportance.MAJOR}
            ][-5:]
            stats = ComparisonStats(
                career_level=latest.career_level,
                health=latest.health,
                relationships=latest.relationships,
                research_impact=latest.research_impact,
                reputation=latest.reputation,
                freedom=latest.freedom,
                stress=latest.stress,
                happiness=latest.happiness,
                discipline=latest.discipline,
                creativity=latest.creativity,
                chaos=latest.chaos,
            )
            components = ScoreComponents(
                wellbeing=round((latest.happiness + latest.health + latest.relationships) / 3),
                sustainability=round((latest.health + latest.freedom + (100 - latest.stress)) / 3),
                career_momentum=round(
                    (latest.career_level + latest.reputation + latest.discipline) / 3
                ),
                research_momentum=round(
                    (latest.research_impact + latest.reputation + latest.creativity) / 3
                ),
                financial_resilience=max(0, min(100, round(50 + latest.net_worth_eur / 2_000))),
            )
            comparisons.append(
                UniverseComparison(
                    universe=UniverseRead.model_validate(universe),
                    current_stats=stats,
                    financial_position=FinancialPosition(
                        monthly_income_eur=latest.monthly_income_eur,
                        net_worth_eur=latest.net_worth_eur,
                    ),
                    location=latest.location,
                    career_summary=f"{latest.career_title}, level {latest.career_level}",
                    major_achievements=achievements,
                    major_regrets=regrets[-5:],
                    key_decisions=decisions[-5:],
                    history=[
                        ComparisonHistoryPoint(
                            year=state.year,
                            happiness=state.happiness,
                            stress=state.stress,
                            net_worth_eur=state.net_worth_eur,
                        )
                        for state in states
                    ],
                    score_components=components,
                )
            )
        return ScenarioComparisonResponse(
            scenario=ScenarioRead.model_validate(scenario), universes=comparisons
        )

    async def create_conversation(
        self, universe_id: UUID, title: str | None, offset: int, limit: int
    ) -> FutureSelfConversationResponse:
        with self.session.begin():
            universe = _required(self.universes.get(universe_id), "Universe", universe_id)
            latest = _required(self.snapshots.latest(universe_id), "Universe state", universe_id)
            context = self._context(universe, latest, self.events.for_universe(universe_id))
            identity = await self._narrative(self.provider.generate_future_self_profile(context))
            conversation = self.conversations.add(
                FutureSelfConversation(
                    universe_id=universe_id,
                    title=title or f"Conversation with {identity.name} in {universe.name}",
                    future_self_age=identity.age,
                    personality_summary=identity.personality_summary,
                )
            )
            return self._conversation_response(conversation, identity, offset, limit)

    async def get_conversation(
        self, conversation_id: UUID, offset: int, limit: int
    ) -> FutureSelfConversationResponse:
        conversation = _required(
            self.conversations.get(conversation_id), "Future-self conversation", conversation_id
        )
        identity = await self._conversation_identity(conversation)
        return self._conversation_response(conversation, identity, offset, limit)

    async def send_future_self_message(
        self, conversation_id: UUID, content: str, offset: int, limit: int
    ) -> FutureSelfConversationResponse:
        with self.session.begin():
            conversation = _required(
                self.conversations.get(conversation_id),
                "Future-self conversation",
                conversation_id,
            )
            universe = _required(
                self.universes.get(conversation.universe_id),
                "Universe",
                conversation.universe_id,
            )
            latest = _required(self.snapshots.latest(universe.id), "Universe state", universe.id)
            context = self._context(universe, latest, self.events.for_universe(universe.id))
            generated_identity = await self._narrative(
                self.provider.generate_future_self_profile(context)
            )
            identity = generated_identity.model_copy(
                update={"personality_summary": conversation.personality_summary}
            )
            history = self.messages.for_conversation(conversation_id)[-12:]
            narrative_history = [
                NarrativeMessage(
                    role="user" if message.role == MessageRole.USER else "future_self",
                    content=message.content,
                )
                for message in history
                if message.role in {MessageRole.USER, MessageRole.FUTURE_SELF}
            ]
            reply = await self._narrative(
                self.provider.generate_future_self_response(
                    FutureSelfReplyRequest(
                        context=context,
                        profile=identity,
                        message=content,
                        conversation_history=narrative_history,
                    )
                )
            )
            self.messages.add(
                FutureSelfMessage(
                    conversation_id=conversation_id,
                    role=MessageRole.USER,
                    content=content,
                    state_snapshot_id=latest.id,
                )
            )
            self.messages.add(
                FutureSelfMessage(
                    conversation_id=conversation_id,
                    role=MessageRole.FUTURE_SELF,
                    content=reply.content,
                    state_snapshot_id=latest.id,
                )
            )
            return self._conversation_response(conversation, identity, offset, limit)

    def _context(
        self,
        universe: Universe,
        state: LifeStateSnapshot | object,
        previous: Sequence[Event],
        unresolved: Sequence[Event] = (),
    ) -> NarrativeContext:
        if not isinstance(state, LifeStateSnapshot):
            # SimulationState is deliberately structural here; the builder accepts both types.
            from app.services.simulation.state import SimulationState

            if not isinstance(state, SimulationState):
                raise TypeError("Unsupported narrative state")
        return self.context_builder.build(
            profile=universe.scenario.profile,
            scenario=universe.scenario,
            universe=universe,
            current_state=state,
            previous_events=previous,
            unresolved_events=unresolved,
        )

    async def _complete_advancement(
        self,
        result: object,
        universe: Universe,
        event: Event,
        generated: GeneratedEvent,
    ) -> AdvancementResponse:
        from app.services.simulation import AdvancementResult

        if not isinstance(result, AdvancementResult) or result.state is None:
            raise InvalidOperationError("Completed advancement did not produce a state")
        previous = self.events.for_universe(universe.id)
        completed_context = self._context(universe, result.state, previous)
        summary = await self._narrative(
            self.provider.generate_year_summary(completed_context, generated)
        )
        self._apply_provider_year_narrative(universe, event, summary)
        generated_artifact = await self._narrative(
            self.provider.generate_artifact(completed_context, generated)
        )
        artifact = self.artifacts.add(
            Artifact(
                universe_id=universe.id,
                event_id=event.id,
                year=result.state.year,
                artifact_type=generated_artifact.artifact_type,
                title=generated_artifact.title,
                content=generated_artifact.content.model_dump(mode="json"),
                artifact_metadata=generated_artifact.metadata.model_dump(mode="json"),
            )
        )
        snapshot = _required(self.snapshots.latest(universe.id), "Universe state", universe.id)
        return AdvancementResponse(
            universe_id=universe.id,
            target_year=result.target_year,
            blocked=False,
            idempotent=result.idempotent,
            state=LifeStateSnapshotRead.model_validate(snapshot),
            event=self._event_response(event),
            summary=summary,
            artifacts=[ArtifactRead.model_validate(artifact)],
        )

    def _advancement_response(self, result: object, event: Event) -> AdvancementResponse:
        from app.services.simulation import AdvancementResult

        if not isinstance(result, AdvancementResult):
            raise TypeError("Unsupported advancement result")
        state = self.snapshots.latest(result.universe_id) if not result.blocked else None
        return AdvancementResponse(
            universe_id=result.universe_id,
            target_year=result.target_year,
            blocked=result.blocked,
            idempotent=result.idempotent,
            state=LifeStateSnapshotRead.model_validate(state) if state is not None else None,
            event=self._event_response(event),
        )

    def _event_response(self, event: Event) -> EventDetailResponse:
        return EventDetailResponse(
            event=EventRead.model_validate(event),
            choices=[
                ChoiceRead.model_validate(choice) for choice in self.choices.for_event(event.id)
            ],
        )

    def _event_definition(self, generated: GeneratedEvent) -> SystemEventDefinition:
        return SystemEventDefinition(
            key=generated.event_key,
            title=generated.title,
            description=generated.description,
            category=generated.category,
            importance=generated.importance,
            effects=generated.automatic_effects or EffectPayload(),
            choices=tuple(
                ChoiceDefinition(
                    label=choice.label,
                    description=choice.description,
                    effects=choice.immediate_effects,
                    delayed_effects=tuple(choice.delayed_effects),
                    requirements=choice.requirements,
                    risk_level=choice.risk_level,
                )
                for choice in generated.choices
            ),
        )

    def _stored_generated_event(self, event: Event) -> GeneratedEvent:
        if event.narrative_key is None:
            raise InvalidOperationError("Stored generated event has no narrative key")
        choices = [
            GeneratedChoice(
                label=choice.label,
                description=choice.description,
                immediate_effects=EffectPayload.model_validate(choice.immediate_effects),
                delayed_effects=[
                    DelayedEffectSpec.model_validate(effect) for effect in choice.delayed_effects
                ],
                requirements=ChoiceRequirements.model_validate(choice.requirements),
                risk_level=choice.risk_level,
            )
            for choice in event.choices
        ]
        return GeneratedEvent(
            event_key=event.narrative_key,
            year=event.year,
            title=event.title,
            description=event.description,
            category=event.category,
            importance=event.importance,
            requires_choice=True,
            choices=choices,
            artifact_suggestions=[],
            narrative_tags=[event.source.value, "persisted", "fictional"],
        )

    def _provider_event_source(self) -> EventSource:
        return (
            EventSource.OPENAI
            if getattr(self.provider, "last_used_provider", "mock") == "openai"
            else EventSource.MOCK
        )

    def _last_narrative_provider_name(self) -> str:
        return getattr(self.provider, "last_used_provider", self.provider.provider_name)

    def _apply_provider_year_narrative(
        self,
        universe: Universe,
        significant_event: Event,
        summary: GeneratedYearSummary,
    ) -> None:
        routine = next(
            (
                event
                for event in self.events.for_universe(universe.id)
                if event.year == summary.year
                and event.id != significant_event.id
                and event.source == EventSource.SYSTEM
            ),
            None,
        )
        if routine is None:
            return
        routine.title = summary.headline
        routine.description = summary.overview
        routine.is_generated = True
        routine.source = self._provider_event_source()

    async def _conversation_identity(
        self, conversation: FutureSelfConversation
    ) -> GeneratedFutureSelfProfile:
        universe = _required(
            self.universes.get(conversation.universe_id), "Universe", conversation.universe_id
        )
        latest = _required(self.snapshots.latest(universe.id), "Universe state", universe.id)
        context = self._context(universe, latest, self.events.for_universe(universe.id))
        identity = await self._narrative(self.provider.generate_future_self_profile(context))
        return identity.model_copy(update={"personality_summary": conversation.personality_summary})

    def _conversation_response(
        self,
        conversation: FutureSelfConversation,
        identity: GeneratedFutureSelfProfile,
        offset: int,
        limit: int,
    ) -> FutureSelfConversationResponse:
        condition = FutureSelfMessage.conversation_id == conversation.id
        statement = (
            select(FutureSelfMessage)
            .where(condition)
            .order_by(FutureSelfMessage.created_at, FutureSelfMessage.id)
        )
        rows = list(self.session.scalars(statement.offset(offset).limit(limit)).all())
        total = (
            self.session.scalar(
                select(func.count()).select_from(FutureSelfMessage).where(condition)
            )
            or 0
        )
        return FutureSelfConversationResponse(
            conversation=FutureSelfConversationRead.model_validate(conversation),
            identity=identity,
            messages=[FutureSelfMessageRead.model_validate(message) for message in rows],
            pagination=_pagination(offset, limit, total),
        )

    @staticmethod
    def _profile_summary(profile: PersonProfile) -> ProfileNarrativeSummary:
        return ProfileNarrativeSummary(
            name=profile.name,
            age=profile.starting_age,
            location=profile.location,
            occupation=profile.occupation,
            education=profile.education,
            biography=profile.biography[:800],
            strengths=profile.strengths[:5],
            interests=profile.interests[:5],
            goals=profile.goals[:4],
            constraints=profile.constraints[:4],
        )

    @staticmethod
    async def _narrative[T](awaitable: Awaitable[T]) -> T:
        try:
            return await awaitable
        except ApplicationServiceError:
            raise
        except Exception as error:
            raise NarrativeUnavailableError(
                "Narrative generation failed; no simulation progress was saved"
            ) from error
