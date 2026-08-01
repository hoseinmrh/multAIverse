from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import build_engine
from app.models.enums import EventStatus, UniverseStatus
from app.repositories import (
    ChoiceRepository,
    DelayedEffectRepository,
    EventRepository,
    LifeStateSnapshotRepository,
    UniverseRepository,
)
from app.services.demo_seed import APPLIED_AI_UNIVERSE_ID, DemoSeedService
from app.services.simulation import SimulationService, UniverseBlockedError


def test_unresolved_choice_blocks_advancement_and_resolution_is_idempotent(
    session: Session,
) -> None:
    DemoSeedService(session).seed()
    service = SimulationService(session)
    snapshots = LifeStateSnapshotRepository(session)

    blocked = service.advance_universe(APPLIED_AI_UNIVERSE_ID)

    assert blocked.blocked is True
    assert blocked.event_id is not None
    assert len(blocked.choice_ids) == 2
    assert len(snapshots.for_universe(APPLIED_AI_UNIVERSE_ID)) == 1
    session.rollback()  # End the repository read transaction before the service owns the next one.
    with pytest.raises(UniverseBlockedError, match="unresolved"):
        service.advance_universe(APPLIED_AI_UNIVERSE_ID)

    resolved = service.resolve_choice(blocked.event_id, blocked.choice_ids[0])
    repeated = service.resolve_choice(blocked.event_id, blocked.choice_ids[0])

    assert resolved.state is not None
    assert resolved.state.year == 2027
    assert repeated.idempotent is True
    assert repeated.state == resolved.state
    assert len(snapshots.for_universe(APPLIED_AI_UNIVERSE_ID)) == 2
    assert EventRepository(session).get(blocked.event_id).status == EventStatus.RESOLVED  # type: ignore[union-attr]
    assert ChoiceRepository(session).get(blocked.choice_ids[0]).selected is True  # type: ignore[union-attr]
    assert UniverseRepository(session).get(APPLIED_AI_UNIVERSE_ID).status == UniverseStatus.ACTIVE  # type: ignore[union-attr]


def test_delayed_choice_effect_is_scheduled_and_consumed_once(session: Session) -> None:
    DemoSeedService(session).seed()
    service = SimulationService(session)
    delayed_repository = DelayedEffectRepository(session)

    first_year = service.advance_universe(APPLIED_AI_UNIVERSE_ID)
    assert first_year.event_id is not None
    service.resolve_choice(first_year.event_id, first_year.choice_ids[0])
    scheduled = delayed_repository.list()
    assert len(scheduled) == 1
    assert scheduled[0].trigger_year == 2029
    assert scheduled[0].applied is False
    delayed_id = scheduled[0].id
    session.rollback()

    current_year = 2027
    while current_year < 2029:
        next_year = service.advance_universe(APPLIED_AI_UNIVERSE_ID)
        if next_year.blocked:
            assert next_year.event_id is not None
            next_year = service.resolve_choice(next_year.event_id, next_year.choice_ids[-1])
        current_year = next_year.target_year

    assert delayed_repository.get(delayed_id).applied is True  # type: ignore[union-attr]


def _run_replay(database_path: Path) -> tuple[tuple[object, ...], ...]:
    engine = build_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    try:
        with factory() as session:
            seed = DemoSeedService(session).seed()
            service = SimulationService(session)
            for universe_id in seed.universe_ids:
                for _ in range(5):
                    advancement = service.advance_universe(universe_id)
                    if advancement.blocked:
                        assert advancement.event_id is not None
                        service.resolve_choice(advancement.event_id, advancement.choice_ids[0])
            snapshots = LifeStateSnapshotRepository(session)
            signature: list[tuple[object, ...]] = []
            for universe_id in seed.universe_ids:
                for state in snapshots.for_universe(universe_id):
                    signature.append(
                        (
                            universe_id,
                            state.year,
                            state.age,
                            state.career_level,
                            state.monthly_income_eur,
                            state.net_worth_eur,
                            state.health,
                            state.relationships,
                            state.research_impact,
                            state.reputation,
                            state.freedom,
                            state.stress,
                            state.happiness,
                            state.discipline,
                            state.creativity,
                            state.chaos,
                            tuple(sorted(state.skills.items())),
                            tuple(state.active_flags),
                        )
                    )
            return tuple(signature)
    finally:
        engine.dispose()


def test_five_year_three_universe_replay_is_reproducible(tmp_path: Path) -> None:
    first = _run_replay(tmp_path / "first.db")
    second = _run_replay(tmp_path / "second.db")

    assert first == second
    assert len(first) == 18
    assert {row[1] for row in first} == {2026, 2027, 2028, 2029, 2030, 2031}
