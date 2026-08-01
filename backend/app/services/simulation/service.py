import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models import Choice, DelayedEffect, Event, LifeStateSnapshot, Universe
from app.models.enums import (
    EventSource,
    EventStatus,
    EventType,
    UniverseStatus,
)
from app.repositories import (
    ChoiceRepository,
    DelayedEffectRepository,
    EventRepository,
    LifeStateSnapshotRepository,
    UniverseRepository,
)
from app.services.simulation.engine import (
    DueEffectInput,
    PreparedYear,
    SimulationEngine,
    YearResult,
)
from app.services.simulation.events import ChoiceDefinition, SystemEventDefinition
from app.services.simulation.schemas import (
    ChoiceRequirements,
    EffectPayload,
    PersistedDelayedEffect,
)
from app.services.simulation.state import SimulationState, requirements_met


class SimulationError(RuntimeError):
    """Base error for safe, transaction-scoped simulation failures."""


class UniverseNotFoundError(SimulationError):
    pass


class UniverseBlockedError(SimulationError):
    pass


class ChoiceResolutionError(SimulationError):
    pass


class ChoiceRequirementsNotMetError(ChoiceResolutionError):
    pass


@dataclass(frozen=True)
class AdvancementResult:
    universe_id: UUID
    target_year: int
    blocked: bool
    event_id: UUID | None
    choice_ids: tuple[UUID, ...]
    state: SimulationState | None
    summary: str | None
    idempotent: bool = False


def state_from_snapshot(snapshot: LifeStateSnapshot) -> SimulationState:
    skills: list[tuple[str, int]] = []
    for name, value in snapshot.skills.items():
        if not isinstance(value, int | float):
            raise SimulationError(f"Stored skill {name!r} is not numeric")
        skills.append((name, int(value)))
    return SimulationState(
        year=snapshot.year,
        age=snapshot.age,
        location=snapshot.location,
        career_title=snapshot.career_title,
        career_level=snapshot.career_level,
        monthly_income_eur=snapshot.monthly_income_eur,
        net_worth_eur=snapshot.net_worth_eur,
        health=snapshot.health,
        relationships=snapshot.relationships,
        research_impact=snapshot.research_impact,
        reputation=snapshot.reputation,
        freedom=snapshot.freedom,
        stress=snapshot.stress,
        happiness=snapshot.happiness,
        discipline=snapshot.discipline,
        creativity=snapshot.creativity,
        chaos=snapshot.chaos,
        skills=tuple(sorted(skills)),
        active_flags=frozenset(snapshot.active_flags),
    )


class SimulationService:
    """Persists pure engine outcomes and owns annual transaction boundaries."""

    def __init__(self, session: Session, engine: SimulationEngine | None = None) -> None:
        self.session = session
        self.engine = engine or SimulationEngine()
        self.universes = UniverseRepository(session)
        self.snapshots = LifeStateSnapshotRepository(session)
        self.events = EventRepository(session)
        self.choices = ChoiceRepository(session)
        self.delayed_effects = DelayedEffectRepository(session)

    def advance_universe(self, universe_id: UUID) -> AdvancementResult:
        with self.session.begin():
            universe = self._require_universe(universe_id)
            pending = self.events.for_universe(universe_id, status=EventStatus.PENDING)
            if pending or universe.status == UniverseStatus.BLOCKED:
                raise UniverseBlockedError("Universe has an unresolved important choice")
            latest = self._require_latest_snapshot(universe)
            due = self.delayed_effects.due_for_universe(universe.id, latest.year + 1)
            prepared = self.engine.prepare_year(
                state_from_snapshot(latest),
                universe_seed=universe.random_seed,
                mode=universe.scenario.simulation_mode,
                due_effects=self._due_inputs(due),
            )
            significant = prepared.significant_event
            if significant.requires_choice:
                event = self._add_event(universe, significant, EventStatus.PENDING)
                choice_ids = tuple(
                    self._add_choice(event, choice).id for choice in significant.choices
                )
                universe.status = UniverseStatus.BLOCKED
                self.session.flush()
                return AdvancementResult(
                    universe_id=universe.id,
                    target_year=prepared.state_before_significant_event.year,
                    blocked=True,
                    event_id=event.id,
                    choice_ids=choice_ids,
                    state=None,
                    summary=None,
                )

            result = self.engine.finalize_year(prepared)
            self._finalize_persistence(universe, prepared, result, due, significant_event=None)
            return AdvancementResult(
                universe_id=universe.id,
                target_year=result.state.year,
                blocked=False,
                event_id=None,
                choice_ids=(),
                state=result.state,
                summary=result.summary,
            )

    def resolve_choice(self, event_id: UUID, choice_id: UUID) -> AdvancementResult:
        with self.session.begin():
            event = self.events.get(event_id)
            choice = self.choices.get(choice_id)
            if event is None or choice is None or choice.event_id != event.id:
                raise ChoiceResolutionError("Choice does not belong to this event")
            universe = self._require_universe(event.universe_id)
            if choice.selected:
                latest = self._require_latest_snapshot(universe)
                return AdvancementResult(
                    universe_id=universe.id,
                    target_year=latest.year,
                    blocked=False,
                    event_id=event.id,
                    choice_ids=(choice.id,),
                    state=state_from_snapshot(latest),
                    summary=None,
                    idempotent=True,
                )
            if event.status == EventStatus.RESOLVED:
                raise ChoiceResolutionError("Event was already resolved with a different choice")

            latest = self._require_latest_snapshot(universe)
            if event.year != latest.year + 1:
                raise ChoiceResolutionError("Choice event is stale for the current universe year")
            due = self.delayed_effects.due_for_universe(universe.id, event.year)
            prepared = self.engine.prepare_year(
                state_from_snapshot(latest),
                universe_seed=universe.random_seed,
                mode=universe.scenario.simulation_mode,
                due_effects=self._due_inputs(due),
            )
            if prepared.significant_event.title != event.title:
                raise ChoiceResolutionError(
                    "Stored choice does not match the reproducible year plan"
                )

            requirements = ChoiceRequirements.model_validate(choice.requirements)
            if not requirements_met(prepared.state_before_significant_event, requirements):
                raise ChoiceRequirementsNotMetError("Choice requirements are not met")
            immediate = EffectPayload.model_validate(choice.immediate_effects)
            result = self.engine.finalize_year(prepared, immediate)

            choice.selected = True
            choice.selected_at = datetime.now(UTC)
            event.status = EventStatus.RESOLVED
            self._schedule_delayed_effects(universe, choice, event.year)
            self._finalize_persistence(universe, prepared, result, due, significant_event=event)
            return AdvancementResult(
                universe_id=universe.id,
                target_year=result.state.year,
                blocked=False,
                event_id=event.id,
                choice_ids=(choice.id,),
                state=result.state,
                summary=result.summary,
            )

    def _require_universe(self, universe_id: UUID) -> Universe:
        universe = self.universes.get(universe_id)
        if universe is None:
            raise UniverseNotFoundError(f"Universe {universe_id} was not found")
        return universe

    def _require_latest_snapshot(self, universe: Universe) -> LifeStateSnapshot:
        latest = self.snapshots.latest(universe.id)
        if latest is None:
            raise SimulationError("Universe has no starting snapshot")
        return latest

    def _due_inputs(self, due: list[DelayedEffect]) -> tuple[DueEffectInput, ...]:
        inputs: list[DueEffectInput] = []
        for delayed in due:
            try:
                persisted = PersistedDelayedEffect.model_validate(delayed.effects)
            except ValidationError:
                persisted = PersistedDelayedEffect(
                    probability=1.0,
                    effects=EffectPayload.model_validate(delayed.effects),
                )
            stable_payload = json.dumps(delayed.effects, sort_keys=True, separators=(",", ":"))
            inputs.append(
                DueEffectInput(
                    key=f"{delayed.trigger_year}:{delayed.description}:{stable_payload}",
                    trigger_year=delayed.trigger_year,
                    probability=persisted.probability,
                    effects=persisted.effects,
                )
            )
        return tuple(inputs)

    def _add_event(
        self,
        universe: Universe,
        definition: SystemEventDefinition,
        status: EventStatus,
    ) -> Event:
        return self.events.add(
            Event(
                universe_id=universe.id,
                year=universe.current_year + 1,
                title=definition.title,
                description=definition.description,
                category=definition.category,
                importance=definition.importance,
                event_type=(
                    EventType.DECISION if definition.requires_choice else EventType.MILESTONE
                ),
                status=status,
                is_generated=False,
                source=EventSource.SYSTEM,
            )
        )

    def _add_choice(self, event: Event, definition: ChoiceDefinition) -> Choice:
        return self.choices.add(
            Choice(
                event_id=event.id,
                label=definition.label,
                description=definition.description,
                immediate_effects=definition.effects.model_dump(mode="json"),
                delayed_effects=[
                    delayed.model_dump(mode="json") for delayed in definition.delayed_effects
                ],
                requirements=definition.requirements.model_dump(mode="json"),
                risk_level=definition.risk_level,
            )
        )

    def _schedule_delayed_effects(
        self,
        universe: Universe,
        choice: Choice,
        choice_year: int,
    ) -> None:
        for raw_delayed in choice.delayed_effects:
            delayed = cast(dict[str, object], raw_delayed)
            trigger_after = delayed.get("trigger_after_years")
            probability = delayed.get("probability", 1.0)
            description = delayed.get("description")
            effects = delayed.get("effects")
            if not isinstance(trigger_after, int) or not isinstance(description, str):
                raise ChoiceResolutionError("Stored delayed effect is malformed")
            persisted = PersistedDelayedEffect.model_validate(
                {"probability": probability, "effects": effects}
            )
            self.delayed_effects.add(
                DelayedEffect(
                    universe_id=universe.id,
                    source_choice_id=choice.id,
                    trigger_year=choice_year + trigger_after,
                    effects=persisted.model_dump(mode="json"),
                    description=description,
                    applied=False,
                )
            )

    def _finalize_persistence(
        self,
        universe: Universe,
        prepared: PreparedYear,
        result: YearResult,
        due: list[DelayedEffect],
        *,
        significant_event: Event | None,
    ) -> None:
        self._add_event(universe, prepared.routine_event, EventStatus.RESOLVED)
        if significant_event is None:
            self._add_event(universe, prepared.significant_event, EventStatus.RESOLVED)
        for delayed in due:
            delayed.applied = True
        state = result.state
        self.snapshots.add(
            LifeStateSnapshot(
                universe_id=universe.id,
                year=state.year,
                age=state.age,
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
                skills=state.skills_dict(),
                active_flags=sorted(state.active_flags),
            )
        )
        universe.current_year = state.year
        universe.current_age = state.age
        universe.status = UniverseStatus.ACTIVE
        self.session.flush()
