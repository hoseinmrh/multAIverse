# Implementation Plan

The source of truth is `docs/PRODUCT_SPEC.md`. Work proceeds one phase at a
time, keeps both applications runnable, and records real verification results
in `docs/PROGRESS.md`.

## Phase 1 — Foundation

- Establish the Git repository and pnpm/uv monorepo tooling.
- Scaffold strict Next.js and FastAPI applications.
- Add a versioned health endpoint and browser connectivity indicator.
- Configure tests, linting, formatting, type checking, and builds.
- Provide shared Makefile commands and setup documentation.

Acceptance: dependencies install from lockfiles; both services start; backend
and frontend tests, lint, format checks, type checks, and builds pass.

## Phase 2 — Domain and persistence

- Add SQLAlchemy entities, Alembic, Pydantic contracts, repositories, and the
  idempotent demo profile/scenario seed.
- Use normalized SQLite tables and JSON only for naturally variable data.
- Preserve immutable snapshots and explicit service-owned transactions.

Status: complete. The seed also persists the three required universe
definitions and their initial snapshots so Phase 3 can begin from a coherent,
replayable state.

## Phase 3 — Deterministic simulation engine

- Add pure state transitions, balance configuration, seeded random streams,
  validated immediate/delayed effects, annual advancement, and idempotent
  choice resolution.
- Maintain high unit-test coverage for deterministic behavior.

Status: complete. The engine uses immutable in-memory values, strict effect
contracts, namespaced seeded random streams, append-only yearly snapshots, and
an idempotent transaction service. The executable demonstration advances all
three demo universes from 2026 through 2031 without a narrative provider.

## Next and later phases

Phase 4 is the mock narrative provider and generated-content schemas.
Domain APIs, the full product interface, comparison,
future-self chat, OpenAI integration, and the quality pass follow Phases 4–9.
Optional enhancements begin only after MVP acceptance criteria pass.

## Key risks

- SQLite write concurrency: keep transactions short and enforce important
  invariants in both services and database constraints.
- Generated data: narrative output never mutates persistence directly and all
  proposed effects pass strict validation.
- Dependency drift: commit `uv.lock` and `pnpm-lock.yaml` and verify production
  builds after upgrades.
- Partial annual updates: apply state changes and choice resolution in one
  transaction when persistence exists.
