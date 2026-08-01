"""Run the three seeded universes for five years with the deterministic engine only."""

from pathlib import Path
from tempfile import TemporaryDirectory

from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import BACKEND_ROOT
from app.db.session import build_engine
from app.repositories import LifeStateSnapshotRepository, UniverseRepository
from app.services.demo_seed import DemoSeedService
from app.services.simulation import SimulationService, UniverseBlockedError


def _migration_config(database_url: str) -> Config:
    config = Config(BACKEND_ROOT / "alembic.ini")
    config.attributes["database_url"] = database_url
    return config


def _simulate_five_years(session: Session, universe_id: object) -> None:
    service = SimulationService(session)
    for _ in range(5):
        result = service.advance_universe(universe_id)  # type: ignore[arg-type]
        if result.blocked:
            if result.event_id is None or not result.choice_ids:
                raise RuntimeError("Blocked year did not provide a resolvable choice")
            result = service.resolve_choice(result.event_id, result.choice_ids[0])
        if result.state is None:
            raise RuntimeError("Year did not produce a state")


def main() -> None:
    with TemporaryDirectory(prefix="multiverse-phase3-") as temporary_directory:
        database_path = Path(temporary_directory) / "demo.db"
        database_url = f"sqlite:///{database_path}"
        command.upgrade(_migration_config(database_url), "head")
        engine = build_engine(database_url)
        session_factory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
        try:
            with session_factory() as session:
                seed = DemoSeedService(session).seed()
                for universe_id in seed.universe_ids:
                    try:
                        _simulate_five_years(session, universe_id)
                    except UniverseBlockedError as error:
                        raise RuntimeError(
                            "Demo failed to resolve a deterministic choice"
                        ) from error

                universes = UniverseRepository(session)
                snapshots = LifeStateSnapshotRepository(session)
                print("Deterministic five-year simulation (no narrative provider / no LLM)")
                print(
                    "Universe             Year  Career  Research  Stress  Happy  Income  Net worth"
                )
                for universe_id in seed.universe_ids:
                    universe = universes.get(universe_id)
                    state = snapshots.latest(universe_id)
                    if universe is None or state is None:
                        raise RuntimeError("Seeded universe disappeared during the demo")
                    print(
                        f"{universe.name:<20} {state.year:>4}  {state.career_level:>6}  "
                        f"{state.research_impact:>8}  {state.stress:>6}  "
                        f"{state.happiness:>5}  €{state.monthly_income_eur:>5}/m  "
                        f"€{state.net_worth_eur:>8}"
                    )
                print("Each universe produced 6 immutable snapshots (2026–2031).")
        finally:
            engine.dispose()


if __name__ == "__main__":
    main()
