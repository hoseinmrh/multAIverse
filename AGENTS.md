# AGENTS.md

## Product

Multiverse is a local-first fictional alternate-life simulation game. Read
`docs/PRODUCT_SPEC.md` completely before significant planning or implementation.
Follow its phases in order and work on only one phase unless explicitly asked.

## Structure

- `frontend/`: Next.js App Router, strict TypeScript, Tailwind, and Vitest.
- `backend/`: FastAPI application managed by `uv`.
- `docs/`: product specification, architecture, design, API, and progress.
- `scripts/`: shared local development helpers.

Persistence, simulation, narrative, and frontend feature code must remain in
their documented boundaries. Do not create cross-layer shortcuts.

## Commands

```bash
make setup
make dev
make backend-dev
make frontend-dev
make test
make lint
make format
make format-check
make typecheck
make build
make seed
make reset-db
```

Run relevant tests, linting, formatting checks, type checks, and builds after
changes. Never claim a command passed unless it was actually run. Keep
`docs/PROGRESS.md` current after every phase.

## Domain invariants

- The deterministic simulation engine owns all state changes.
- Narrative providers never write directly to the database or mutate state.
- Every proposed effect is validated and capped before application.
- Important choice resolution is idempotent.
- Life-state snapshots are immutable.
- Seeded simulation never uses uncontrolled global randomness.
- Do not execute generated narrative content as code.

## Persistence rules

- Use SQLAlchemy 2 typed models and Alembic migrations.
- Never create production tables implicitly at application startup.
- Repositories receive sessions but do not commit; services own transactions.
- Use normalized columns for domain data and JSON only for naturally variable
  effects, skills, flags, and artifact metadata.
- Add and review a migration whenever persisted schema changes.

## Security

- OpenAI credentials remain backend-only.
- Mock narrative mode must work without an API key.
- Never expose secrets in logs, frontend responses, URLs, or `NEXT_PUBLIC_`
  variables.
- Validate API inputs and generated content; never let generated text control
  code execution, file paths, or shell commands.

## Definition of done

A task is complete only when requested behavior and relevant tests exist, all
applicable verification commands pass, documentation is updated, and the
application remains runnable. Do not replace working implementations with
placeholders or begin optional work before MVP criteria pass.
