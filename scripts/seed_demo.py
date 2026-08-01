"""Migrate and idempotently seed the local demo database."""

from alembic import command
from alembic.config import Config

from app.core.config import BACKEND_ROOT
from app.db.session import SessionLocal
from app.services.demo_seed import DemoSeedService


def migration_config() -> Config:
    return Config(BACKEND_ROOT / "alembic.ini")


def main() -> None:
    command.upgrade(migration_config(), "head")
    with SessionLocal() as session:
        result = DemoSeedService(session).seed()
    print(
        "Seeded demo profile, scenario, and three universes "
        f"(profile={result.profile_id}, scenario={result.scenario_id})."
    )


if __name__ == "__main__":
    main()
