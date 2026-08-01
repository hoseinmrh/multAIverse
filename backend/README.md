# Multiverse backend

FastAPI and SQLAlchemy backend for the local-first Multiverse application. Run
it through the root Makefile commands documented in `../README.md`.

Alembic owns the production schema. From this directory:

```bash
uv run alembic upgrade head
uv run alembic current
uv run alembic check
```

From the repository root, `make seed` upgrades to the current migration and
idempotently adds the demo data. `make reset-db` downgrades to an empty schema,
upgrades to head, and restores the demo. Resetting is destructive to local
simulation data.

Application startup never creates tables implicitly. Repositories only flush;
application services own transactions and commits.
