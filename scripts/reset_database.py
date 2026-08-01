"""Rebuild the local schema through Alembic, then restore the demo seed."""

from alembic import command
from seed_demo import migration_config

from app.db.session import SessionLocal
from app.services.demo_seed import DemoSeedService


def main() -> None:
    config = migration_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    with SessionLocal() as session:
        DemoSeedService(session).seed()
    print("Reset the database to the current migration and restored the demo seed.")


if __name__ == "__main__":
    main()
