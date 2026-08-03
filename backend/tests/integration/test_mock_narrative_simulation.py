from dataclasses import dataclass

import pytest
from sqlalchemy.orm import Session

from app.models import PersonProfile, Scenario, Universe
from app.repositories import (
    LifeStateSnapshotRepository,
    PersonProfileRepository,
    ScenarioRepository,
    UniverseRepository,
)
from app.services.demo_seed import DemoSeedService
from app.services.narrative import (
    GeneratedEvent,
    MockNarrativeProvider,
    NarrativeContextBuilder,
)
from app.services.simulation import SimulationEngine, SimulationState, state_from_snapshot


@dataclass(frozen=True)
class _NarrativeReplay:
    universe_name: str
    state: SimulationState
    event_keys: tuple[str, ...]
    summaries: tuple[str, ...]
    artifacts: tuple[str, ...]


def _required[T](value: T | None) -> T:
    assert value is not None
    return value


async def _run_universe(
    profile: PersonProfile,
    scenario: Scenario,
    universe: Universe,
    initial_state: SimulationState,
) -> _NarrativeReplay:
    provider = MockNarrativeProvider()
    builder = NarrativeContextBuilder()
    engine = SimulationEngine()
    state = initial_state
    events: list[GeneratedEvent] = []
    summaries: list[str] = []
    artifacts: list[str] = []
    for _ in range(5):
        context = builder.build(
            profile=profile,
            scenario=scenario,
            universe=universe,
            current_state=state,
            previous_events=events,
        )
        event = await provider.generate_significant_event(context)
        prepared = engine.prepare_year(
            state,
            universe_seed=universe.random_seed,
            mode=scenario.simulation_mode,
        )
        state = engine.finalize_year(prepared, event.choices[0].immediate_effects).state
        events.append(event)
        completed = builder.build(
            profile=profile,
            scenario=scenario,
            universe=universe,
            current_state=state,
            previous_events=events,
        )
        summaries.append((await provider.generate_year_summary(completed, event)).headline)
        artifacts.append((await provider.generate_artifact(completed, event)).title)
    return _NarrativeReplay(
        universe_name=universe.name,
        state=state,
        event_keys=tuple(event.event_key for event in events),
        summaries=tuple(summaries),
        artifacts=tuple(artifacts),
    )


@pytest.mark.anyio
async def test_all_three_seeded_universes_run_five_mock_narrative_years(
    session: Session,
) -> None:
    seed = DemoSeedService(session).seed()
    profile = _required(PersonProfileRepository(session).get(seed.profile_id))
    scenario = _required(ScenarioRepository(session).get(seed.scenario_id))
    universes = UniverseRepository(session)
    snapshots = LifeStateSnapshotRepository(session)

    first: list[_NarrativeReplay] = []
    second: list[_NarrativeReplay] = []
    for target in (first, second):
        for universe_id in seed.universe_ids:
            universe = _required(universes.get(universe_id))
            initial = state_from_snapshot(_required(snapshots.latest(universe_id)))
            target.append(await _run_universe(profile, scenario, universe, initial))

    assert first == second
    assert {result.universe_name for result in first} == {
        "Applied AI Leader",
        "Robotics Researcher",
        "Startup Founder",
    }
    assert all(result.state.year == 2031 for result in first)
    assert all(len(set(result.event_keys)) == 5 for result in first)
    assert all(len(result.summaries) == len(result.artifacts) == 5 for result in first)
