"""Simulate all seeded universes for five years with the offline mock provider."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import BACKEND_ROOT
from app.db.session import build_engine
from app.models import PersonProfile, Scenario, Universe
from app.repositories import (
    LifeStateSnapshotRepository,
    PersonProfileRepository,
    ScenarioRepository,
    UniverseRepository,
)
from app.services.demo_seed import DemoSeedService
from app.services.narrative import (
    FutureSelfReplyRequest,
    GeneratedEvent,
    MockNarrativeProvider,
    NarrativeContextBuilder,
    UniverseBranchRequest,
)
from app.services.narrative.schemas import FutureSelfMessage
from app.services.simulation import (
    DueEffectInput,
    SeededRandom,
    SimulationEngine,
    SimulationState,
    state_from_snapshot,
)


@dataclass(frozen=True)
class DemoUniverseResult:
    name: str
    state: SimulationState
    events: tuple[GeneratedEvent, ...]
    summary_headlines: tuple[str, ...]
    artifact_titles: tuple[str, ...]
    future_self_reply: str


def _migration_config(database_url: str) -> Config:
    config = Config(BACKEND_ROOT / "alembic.ini")
    config.attributes["database_url"] = database_url
    return config


def _required[T](value: T | None, label: str) -> T:
    if value is None:
        raise RuntimeError(f"Seeded {label} was not found")
    return value


async def simulate_universe(
    *,
    profile: PersonProfile,
    scenario: Scenario,
    universe: Universe,
    initial_state: SimulationState,
) -> DemoUniverseResult:
    provider = MockNarrativeProvider()
    context_builder = NarrativeContextBuilder()
    engine = SimulationEngine()
    state = initial_state
    history: list[GeneratedEvent] = []
    summaries: list[str] = []
    artifacts: list[str] = []
    pending_effects: list[DueEffectInput] = []

    for _ in range(5):
        context = context_builder.build(
            profile=profile,
            scenario=scenario,
            universe=universe,
            current_state=state,
            previous_events=history,
        )
        event = await provider.generate_significant_event(context)
        due = tuple(effect for effect in pending_effects if effect.trigger_year <= event.year)
        pending_effects = [effect for effect in pending_effects if effect.trigger_year > event.year]
        prepared = engine.prepare_year(
            state,
            universe_seed=universe.random_seed,
            mode=scenario.simulation_mode,
            due_effects=due,
        )
        choice = SeededRandom(universe.random_seed).choice(
            event.choices,
            event.year,
            event.event_key,
            "demo-choice",
        )
        result = engine.finalize_year(prepared, choice.immediate_effects)
        for index, delayed in enumerate(choice.delayed_effects):
            pending_effects.append(
                DueEffectInput(
                    key=f"{event.event_key}:{index}",
                    trigger_year=event.year + delayed.trigger_after_years,
                    probability=delayed.probability,
                    effects=delayed.effects,
                )
            )
        state = result.state
        history.append(event)
        completed_context = context_builder.build(
            profile=profile,
            scenario=scenario,
            universe=universe,
            current_state=state,
            previous_events=history,
        )
        summary = await provider.generate_year_summary(completed_context, event)
        artifact = await provider.generate_artifact(completed_context, event)
        summaries.append(summary.headline)
        artifacts.append(artifact.title)

    final_context = context_builder.build(
        profile=profile,
        scenario=scenario,
        universe=universe,
        current_state=state,
        previous_events=history,
    )
    future_profile = await provider.generate_future_self_profile(final_context)
    reply = await provider.generate_future_self_response(
        FutureSelfReplyRequest(
            context=final_context,
            profile=future_profile,
            message="Was this path worth it, and what are you proud of?",
            conversation_history=[
                FutureSelfMessage(
                    role="user",
                    content="Was this path worth it, and what are you proud of?",
                )
            ],
        )
    )
    return DemoUniverseResult(
        name=universe.name,
        state=state,
        events=tuple(history),
        summary_headlines=tuple(summaries),
        artifact_titles=tuple(artifacts),
        future_self_reply=reply.content,
    )


async def run_demo(session: Session) -> tuple[DemoUniverseResult, ...]:
    seed = DemoSeedService(session).seed()
    profiles = PersonProfileRepository(session)
    scenarios = ScenarioRepository(session)
    universes = UniverseRepository(session)
    snapshots = LifeStateSnapshotRepository(session)
    profile = _required(profiles.get(seed.profile_id), "profile")
    scenario = _required(scenarios.get(seed.scenario_id), "scenario")
    provider = MockNarrativeProvider()

    first_universe = _required(universes.get(seed.universe_ids[0]), "universe")
    initial_context = NarrativeContextBuilder().build(
        profile=profile,
        scenario=scenario,
        universe=first_universe,
        current_state=_required(snapshots.latest(first_universe.id), "snapshot"),
    )
    branches = await provider.generate_universe_branches(
        UniverseBranchRequest(
            profile=initial_context.profile,
            decision_question=scenario.decision_question,
            scenario_seed=scenario.seed,
            simulation_mode=scenario.simulation_mode,
        )
    )
    if tuple(branch.name for branch in branches) != (
        "Applied AI Leader",
        "Robotics Researcher",
        "Startup Founder",
    ):
        raise RuntimeError("Mock provider did not generate the required demo branches")

    results: list[DemoUniverseResult] = []
    for universe_id in seed.universe_ids:
        universe = _required(universes.get(universe_id), "universe")
        snapshot = _required(snapshots.latest(universe_id), "snapshot")
        results.append(
            await simulate_universe(
                profile=profile,
                scenario=scenario,
                universe=universe,
                initial_state=state_from_snapshot(snapshot),
            )
        )
    return tuple(results)


async def _main() -> None:
    with TemporaryDirectory(prefix="multiverse-phase4-") as temporary_directory:
        database_path = Path(temporary_directory) / "demo.db"
        database_url = f"sqlite:///{database_path}"
        command.upgrade(_migration_config(database_url), "head")
        database_engine = build_engine(database_url)
        factory = sessionmaker(
            bind=database_engine,
            class_=Session,
            expire_on_commit=False,
        )
        try:
            with factory() as session:
                results = await run_demo(session)
                print("Five-year narrative simulation (MockNarrativeProvider; offline)")
                print("Universe             Year  Events  Artifacts  Stress  Happy  Career")
                for result in results:
                    print(
                        f"{result.name:<20} {result.state.year:>4}  {len(result.events):>6}  "
                        f"{len(result.artifact_titles):>9}  {result.state.stress:>6}  "
                        f"{result.state.happiness:>5}  {result.state.career_level:>6}"
                    )
                print("All narratives, summaries, artifacts, and replies used the mock provider.")
                print("No API key or network access was used.")
        finally:
            database_engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
