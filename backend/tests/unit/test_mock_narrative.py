from dataclasses import replace

import pytest
from sqlalchemy.orm import Session

from app.models import PersonProfile, Scenario, Universe
from app.models.enums import ArtifactType, EventCategory, SimulationMode
from app.repositories import (
    LifeStateSnapshotRepository,
    PersonProfileRepository,
    ScenarioRepository,
    UniverseRepository,
)
from app.services.demo_seed import APPLIED_AI_UNIVERSE_ID, DemoSeedService
from app.services.narrative import (
    FutureSelfReplyRequest,
    GeneratedEvent,
    MockNarrativeProvider,
    NarrativeContext,
    NarrativeContextBuilder,
    NarrativeProvider,
    NarrativeProviderConfigurationError,
    OpenAINarrativeProvider,
    UniverseBranchRequest,
    create_narrative_provider,
)
from app.services.narrative.mock import EVENT_TEMPLATES
from app.services.narrative.schemas import (
    AcademicAbstractContent,
    CompanyAnnouncementContent,
    DiaryEntryContent,
    EmailContent,
    FutureSelfMessage,
    NewsArticleContent,
    SocialPostContent,
)
from app.services.simulation import SimulationState, state_from_snapshot


def _required[T](value: T | None) -> T:
    assert value is not None
    return value


def _seeded_context(
    session: Session,
) -> tuple[NarrativeContext, PersonProfile, Scenario, Universe, SimulationState]:
    seed = DemoSeedService(session).seed()
    profile = _required(PersonProfileRepository(session).get(seed.profile_id))
    scenario = _required(ScenarioRepository(session).get(seed.scenario_id))
    universe = _required(UniverseRepository(session).get(APPLIED_AI_UNIVERSE_ID))
    snapshot = _required(LifeStateSnapshotRepository(session).latest(universe.id))
    state = state_from_snapshot(snapshot)
    context = NarrativeContextBuilder().build(
        profile=profile,
        scenario=scenario,
        universe=universe,
        current_state=state,
    )
    return context, profile, scenario, universe, state


def _advance_context(context: NarrativeContext, events: list[GeneratedEvent]) -> NarrativeContext:
    next_year = context.current_year + 1
    payload = context.model_dump()
    payload["current_year"] = next_year
    payload["current_state"]["year"] = next_year
    payload["current_state"]["age"] = context.current_state.age + 1
    payload["previous_event_keys"] = [event.event_key for event in events]
    payload["last_major_events"] = [
        {
            "event_key": event.event_key,
            "year": event.year,
            "title": event.title,
            "description": event.description,
            "category": event.category,
            "importance": event.importance,
        }
        for event in events[-3:]
    ]
    return NarrativeContext.model_validate(payload)


@pytest.mark.anyio
async def test_mock_provider_protocol_and_branch_generation_are_reproducible(
    session: Session,
) -> None:
    context, _, scenario, _, _ = _seeded_context(session)
    provider = MockNarrativeProvider()
    assert isinstance(provider, NarrativeProvider)
    request = UniverseBranchRequest(
        profile=context.profile,
        decision_question=scenario.decision_question,
        scenario_seed=scenario.seed,
        simulation_mode=scenario.simulation_mode,
    )

    first = await provider.generate_universe_branches(request)
    second = await provider.generate_universe_branches(request)

    assert first == second
    assert [branch.name for branch in first] == [
        "Applied AI Leader",
        "Robotics Researcher",
        "Startup Founder",
    ]
    assert len({branch.proposed_initial_state.active_flags[0] for branch in first}) == 3
    assert all(branch.model_dump(mode="json") for branch in first)


@pytest.mark.anyio
async def test_mock_branches_honor_non_demo_directions(session: Session) -> None:
    context, _, scenario, _, _ = _seeded_context(session)
    request = UniverseBranchRequest(
        profile=context.profile.model_copy(update={"occupation": "Financial Analyst"}),
        decision_question="Should I study, focus on my career, or create content?",
        scenario_seed=scenario.seed,
        simulation_mode=SimulationMode.CINEMATIC,
        branch_directions=[
            "Stay in University",
            "Focus on Career as a Financial Analyst",
            "Become a Content Creator",
        ],
    )

    branches = await MockNarrativeProvider().generate_universe_branches(request)

    assert [branch.name for branch in branches] == request.branch_directions
    assert [branch.proposed_initial_state.career_title for branch in branches] == [
        "Graduate Student",
        "Financial Analyst",
        "Content Creator",
    ]
    assert all("AI" not in branch.subtitle for branch in branches)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("flag", "direction", "career", "event_prefix"),
    [
        ("education_path", "Stay in University", "Graduate Student", "custom-education-"),
        (
            "career_path",
            "Focus on Career as a Financial Analyst",
            "Financial Analyst",
            "custom-career-",
        ),
        ("creator_path", "Become a Content Creator", "Content Creator", "custom-creator-"),
    ],
)
async def test_mock_events_use_custom_path_catalogues(
    session: Session,
    flag: str,
    direction: str,
    career: str,
    event_prefix: str,
) -> None:
    context, _, _, _, _ = _seeded_context(session)
    payload = context.model_dump(mode="python")
    payload["universe"]["starting_direction"] = direction
    payload["current_state"]["career_title"] = career
    payload["current_state"]["active_flags"] = [flag]
    custom_context = NarrativeContext.model_validate(payload)

    event = await MockNarrativeProvider().generate_significant_event(custom_context)

    assert event.event_key.startswith(event_prefix)
    assert "robot" not in f"{event.title} {event.description}".casefold()
    assert "ai programme" not in event.description.casefold()


@pytest.mark.anyio
async def test_events_are_seeded_reproducible_and_do_not_repeat(session: Session) -> None:
    context, _, _, _, _ = _seeded_context(session)
    provider = MockNarrativeProvider()
    first = await provider.generate_significant_event(context)
    assert first == await provider.generate_significant_event(context)

    events: list[GeneratedEvent] = []
    for _ in range(5):
        event = await provider.generate_significant_event(context)
        events.append(event)
        context = _advance_context(context, events)

    assert len({event.event_key for event in events}) == 5
    assert len({event.title for event in events}) == 5
    assert all(event.requires_choice and len(event.choices) == 2 for event in events)


@pytest.mark.anyio
async def test_event_selection_responds_to_state_and_simulation_mode(session: Session) -> None:
    context, _, _, _, _ = _seeded_context(session)
    provider = MockNarrativeProvider()
    strained_state = context.current_state.model_copy(update={"health": 42, "stress": 91})
    strained = context.model_copy(update={"current_state": strained_state})
    event = await provider.generate_significant_event(strained)
    assert event.category in {EventCategory.HEALTH, EventCategory.CRISIS}

    descriptions: set[str] = set()
    for mode in SimulationMode:
        mode_context = context.model_copy(update={"simulation_mode": mode})
        mode_event = await provider.generate_significant_event(mode_context)
        descriptions.add(mode_event.description)
        assert mode.value in mode_event.narrative_tags
        if mode == SimulationMode.CHAOS:
            assert mode_event.category == EventCategory.RANDOM
    assert len(descriptions) == len(SimulationMode)


def test_mock_catalogue_supports_required_event_categories() -> None:
    supported = {template.category for template in EVENT_TEMPLATES}
    assert {
        EventCategory.CAREER,
        EventCategory.RESEARCH,
        EventCategory.STARTUP,
        EventCategory.FINANCE,
        EventCategory.HEALTH,
        EventCategory.RELATIONSHIP,
        EventCategory.OPPORTUNITY,
        EventCategory.CRISIS,
    }.issubset(supported)


def test_provider_factory_keeps_mock_default_and_requires_complete_openai_config() -> None:
    assert isinstance(create_narrative_provider(" MOCK "), MockNarrativeProvider)
    assert isinstance(create_narrative_provider("openai"), MockNarrativeProvider)
    with pytest.raises(NarrativeProviderConfigurationError, match="not fully configured"):
        create_narrative_provider("openai", fallback_to_mock=False)
    assert isinstance(
        create_narrative_provider(
            "openai", api_key="sk-test-only", model="test-model", fallback_to_mock=False
        ),
        OpenAINarrativeProvider,
    )


@pytest.mark.anyio
async def test_year_summaries_and_all_structured_artifacts_validate(session: Session) -> None:
    context, _, _, _, _ = _seeded_context(session)
    provider = MockNarrativeProvider()
    event = await provider.generate_significant_event(context)
    completed_context = _advance_context(context, [event])
    summary = await provider.generate_year_summary(completed_context, event)
    assert summary.year == 2027
    assert event.title in summary.key_developments

    expected_content = {
        ArtifactType.NEWS_ARTICLE: NewsArticleContent,
        ArtifactType.ACADEMIC_ABSTRACT: AcademicAbstractContent,
        ArtifactType.COMPANY_ANNOUNCEMENT: CompanyAnnouncementContent,
        ArtifactType.DIARY_ENTRY: DiaryEntryContent,
        ArtifactType.EMAIL: EmailContent,
        ArtifactType.SOCIAL_MEDIA_POST: SocialPostContent,
    }
    for artifact_type, content_type in expected_content.items():
        artifact = await provider.generate_artifact(completed_context, event, artifact_type)
        assert artifact.artifact_type == artifact_type
        assert isinstance(artifact.content, content_type)
        assert artifact.metadata.is_fictional is True


@pytest.mark.anyio
async def test_future_self_is_stable_and_references_only_recorded_timeline(
    session: Session,
) -> None:
    context, _, _, _, _ = _seeded_context(session)
    provider = MockNarrativeProvider()
    events: list[GeneratedEvent] = []
    for _ in range(3):
        event = await provider.generate_significant_event(context)
        events.append(event)
        context = _advance_context(context, events)

    first_profile = await provider.generate_future_self_profile(context)
    second_profile = await provider.generate_future_self_profile(context)
    assert first_profile == second_profile
    request = FutureSelfReplyRequest(
        context=context,
        profile=first_profile,
        message="What do you regret and what did you sacrifice?",
        conversation_history=[
            FutureSelfMessage(
                role="user",
                content="What do you regret and what did you sacrifice?",
            )
        ],
    )
    reply = await provider.generate_future_self_response(request)
    assert reply.referenced_event_keys
    assert set(reply.referenced_event_keys).issubset(context.previous_event_keys)
    assert first_profile.greatest_regret in reply.content
    assert reply.fictional_character is True


@pytest.mark.anyio
async def test_context_builder_bounds_history_and_uses_no_persistence_service(
    session: Session,
) -> None:
    context, profile, scenario, universe, state = _seeded_context(session)
    provider = MockNarrativeProvider()
    assert not hasattr(provider, "session")
    assert not hasattr(provider, "commit")
    events: list[GeneratedEvent] = []
    current = context

    for _ in range(5):
        event = await provider.generate_significant_event(current)
        events.append(event)
        current = _advance_context(current, events)
    rebuilt = NarrativeContextBuilder().build(
        profile=profile,
        scenario=scenario,
        universe=universe,
        current_state=replace(state, year=2031, age=30),
        previous_events=events,
    )
    assert len(rebuilt.last_major_events) == 3
    assert rebuilt.previous_event_keys == [event.event_key for event in events]
    assert len(rebuilt.profile.strengths) <= 5
    assert rebuilt.allowed_effect_fields.stats
