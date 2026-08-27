# Contributing to Multiverse

Thank you for improving Multiverse. The project is a local-first fictional
alternate-life simulation game with strict boundaries between deterministic
state changes and generated narrative.

Read `AGENTS.md` and `docs/PRODUCT_SPEC.md` before making a significant change.
Follow the implementation phases in `docs/PLAN.md`; work on one phase at a time
unless an issue or maintainer explicitly defines a narrower cross-cutting task.

## Development setup

Use the pinned tool versions where possible. From a clone of the repository:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
make setup
make seed
make dev
```

The default mock narrative provider needs no API key. Dependency installation
does require network access on a machine without populated package caches.

## Making a change

1. Create a focused branch from `main`.
2. Keep the change within the documented architecture and phase.
3. Add tests for changed behavior, including failure and idempotency cases where
   relevant.
4. Add an Alembic migration for every persisted schema change. Application
   startup must never create production tables implicitly.
5. Update documentation and `docs/PROGRESS.md` when behavior, setup, APIs, or
   project status changes.
6. Run the applicable checks before opening a pull request.

The complete local verification set is:

```bash
make test
make lint
make format-check
make typecheck
make build
```

Use `make format` to apply Ruff and Prettier formatting. If persistence changed,
also run the following from `backend/`:

```bash
uv run alembic upgrade head
uv run alembic current
uv run alembic check
```

## Non-negotiable boundaries

- The deterministic engine owns all simulation state changes.
- Narrative providers do not access repositories, commit transactions, or
  mutate state.
- Every proposed effect is schema-validated, allowlisted, and capped.
- Important choice selection is idempotent.
- Life-state snapshots are immutable.
- Seeded behavior never uses uncontrolled global randomness.
- OpenAI credentials stay backend-only, and mock mode remains fully usable.
- Generated content is data and must never be executed as code or used to
  control file paths or shell commands.

## Pull requests

Keep pull requests small enough to review. Explain the outcome, note migrations
or compatibility concerns, and list exact verification commands. Do not claim a
check passed unless you ran it. CI repeats backend and frontend tests, linting,
format checks, strict type checks, migration drift checks, and builds.

Never include a real API key, a local `.env`, a database, personal simulation
data, or generated build output. For vulnerabilities, follow `SECURITY.md`
instead of opening a public issue.
