from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, func, inspect, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import BACKEND_ROOT
from app.db.session import build_engine
from app.models import LifeStateSnapshot, PersonProfile, Scenario, Universe
from app.models.enums import SimulationMode
from app.services.demo_seed import (
    APPLIED_AI_UNIVERSE_ID,
    DEMO_PROFILE_ID,
    DEMO_SCENARIO_ID,
    DemoSeedService,
)

EXPECTED_TABLES = {
    "alembic_version",
    "artifacts",
    "choices",
    "delayed_effects",
    "events",
    "future_self_conversations",
    "future_self_messages",
    "life_state_snapshots",
    "person_profiles",
    "scenarios",
    "universes",
}


def _migration_config(database_url: str) -> Config:
    config = Config(BACKEND_ROOT / "alembic.ini")
    config.attributes["database_url"] = database_url
    return config


def test_initial_migration_upgrades_and_downgrades_a_clean_database(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    config = _migration_config(database_url)

    command.upgrade(config, "head")

    inspection_engine = create_engine(database_url)
    assert set(inspect(inspection_engine).get_table_names()) == EXPECTED_TABLES
    with inspection_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(PersonProfile)) == 0
    inspection_engine.dispose()

    command.downgrade(config, "base")
    downgraded_engine = create_engine(database_url)
    assert set(inspect(downgraded_engine).get_table_names()) <= {"alembic_version"}
    downgraded_engine.dispose()


def test_demo_seed_is_complete_and_idempotent_on_migrated_database(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'seed.db'}"
    command.upgrade(_migration_config(database_url), "head")
    engine: Engine = build_engine(database_url)
    factory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

    with factory() as session:
        first_result = DemoSeedService(session).seed()
    with factory() as session:
        second_result = DemoSeedService(session).seed()

    assert first_result == second_result
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(PersonProfile)) == 1
        assert session.scalar(select(func.count()).select_from(Scenario)) == 1
        assert session.scalar(select(func.count()).select_from(Universe)) == 3
        assert session.scalar(select(func.count()).select_from(LifeStateSnapshot)) == 3

        profile = session.get(PersonProfile, DEMO_PROFILE_ID)
        assert profile is not None
        assert profile.name == "Hosein"
        assert profile.starting_year == 2026
        assert profile.starting_age == 25
        assert profile.location == "Milan"
        assert "Quantum-inspired optimization" in profile.interests

        scenario = session.get(Scenario, DEMO_SCENARIO_ID)
        assert scenario is not None
        assert scenario.decision_question == "What should Hosein prioritize after graduation?"
        assert scenario.number_of_universes == 3
        assert scenario.simulation_mode is SimulationMode.REALISTIC

        universes = list(session.scalars(select(Universe).order_by(Universe.slug)))
        assert {universe.name for universe in universes} == {
            "Applied AI Leader",
            "Robotics Researcher",
            "Startup Founder",
        }
        assert len({universe.random_seed for universe in universes}) == 3
        assert all(len(universe.snapshots) == 1 for universe in universes)

        applied_snapshot = session.scalar(
            select(LifeStateSnapshot).where(LifeStateSnapshot.universe_id == APPLIED_AI_UNIVERSE_ID)
        )
        assert applied_snapshot is not None
        assert applied_snapshot.career_title == "AI Research Engineer"
        assert applied_snapshot.active_flags == ["industry_path", "masters_completed"]

    with pytest.raises(IntegrityError, match="life-state snapshots are immutable"):
        with engine.begin() as connection:
            connection.execute(
                update(LifeStateSnapshot)
                .where(LifeStateSnapshot.id == applied_snapshot.id)
                .values(happiness=1)
            )

    engine.dispose()
