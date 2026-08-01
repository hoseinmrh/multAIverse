# Progress

## Current phase

Phase 3 — Deterministic simulation engine: **complete** (2026-08-01)

## Phase 3 completed work

- Added a pure deterministic engine isolated from FastAPI, SQLAlchemy, and all
  narrative-provider code.
- Added namespaced SHA-256 seed derivation and local seeded PRNG streams for
  event selection, market timing, path outcomes, and probabilistic delayed
  consequences. The engine never uses global randomness.
- Added a deeply immutable in-memory simulation state and append-only persisted
  yearly snapshots.
- Added strict effect, finance, delayed-effect, and choice-requirement schemas;
  unknown statistics, extra fields, malformed values, and invalid probabilities
  are rejected.
- Added immediate effects, delayed scheduling and application, seeded
  probability resolution, flags, skills, per-effect caps, diminishing returns,
  stronger high-stress penalties, aggregate annual caps, and 0–100 clamping.
- Added yearly baseline recovery, prolonged extreme-stress health damage,
  nonlinear happiness, burnout risk, career/research/startup momentum, and
  mode-adjusted success/setback selection with nonzero outcome tails.
- Added annual income growth, bounded saving behavior, startup runway pressure,
  positive asset returns, debt interest, and net-worth updates without treating
  money as a proxy for happiness.
- Added deterministic routine/significant system events and choices. These are
  static engine configuration; no narrative provider or LLM is present.
- Added a transaction-owning simulation service that blocks unresolved choices,
  validates requirements, applies selections atomically, schedules delayed
  effects, advances universe cursors, and appends one final snapshot per year.
- Made choice resolution idempotent: selecting the same choice again returns the
  existing state without applying any effect twice, while conflicting choices
  are rejected.
- Added `make simulation-demo`, which migrates an ephemeral database, seeds the
  three required universes, auto-selects deterministic choices, advances each
  five years from 2026 to 2031, prints final results, and uses no LLM.
- Added unit/integration coverage for seeded replay, immutability, effect
  validation/application, delayed and probabilistic effects, clamping, stress,
  happiness, burnout, finances, all momentum families, unresolved blocking,
  idempotency, and full three-universe five-year reproducibility.
- Updated the root/backend guides, implementation plan, game design, and
  architecture documentation for Phase 3.

## Prior completed work

- Added SQLAlchemy 2 typed entities for person profiles, scenarios, universes,
  life-state snapshots, events, choices, delayed effects, artifacts, and
  future-self conversations/messages.
- Added UUID identifiers, relationships, cascade behavior, enum constraints,
  normalized-stat checks, aggregate uniqueness, foreign-key enforcement, and a
  partial unique index that permits at most one selected choice per event.
- Kept scalar domain state in normalized columns and limited JSON to variable
  lists, themes, effects, requirements, skills, flags, and type-specific
  artifact content/metadata.
- Made life-state history append-only through its repository, blocked ORM
  updates, and added a SQLite migration trigger that rejects direct snapshot
  updates.
- Added strict Pydantic create/read contracts for every Phase 2 entity plus a
  partial profile-update contract.
- Added session-scoped repositories for every entity. Repositories flush but do
  not commit, leaving transaction ownership with application services.
- Configured SQLite sessions with foreign keys enabled and a stable,
  working-directory-independent default database path.
- Added Alembic configuration and initial revision `5bd72efdd0ea`, covering all
  ten domain tables, indexes, constraints, and downgrade behavior. Application
  startup does not create production tables.
- Added an idempotent, transaction-owning demo seed service with stable UUIDs
  and deterministic integer seeds.
- Seeded the specified Hosein profile, the “After Graduation” scenario, the
  Applied AI Leader, Robotics Researcher, and Startup Founder universes, and an
  internally complete 2026 snapshot for each branch.
- Implemented `make seed` and destructive `make reset-db` workflows through
  Alembic, and documented direct migration usage and troubleshooting.
- Added unit and integration coverage for Pydantic validation, repository
  transaction behavior, all entity round-trips, snapshot immutability, clean
  migration upgrade/downgrade, complete seed content, and seed idempotency.
- Updated the root/backend setup guides, architecture, plan, environment sample,
  and quality commands for Phase 2.

## Phase 3 verification

All final checks passed:

- `cd backend && uv run pytest` — 24 backend tests passed.
- `cd backend && uv run ruff check app tests migrations ../scripts` — passed.
- `cd backend && uv run ruff format --check app tests migrations ../scripts` — passed.
- `cd backend && uv run mypy app tests ../scripts` — strict type checking passed.
- `cd backend && uv run alembic check` — no schema drift or new upgrade
  operations detected.
- `cd backend && uv run python -m compileall -q app migrations ../scripts` — passed.
- `make simulation-demo` — all three universes reached 2031 with six immutable
  snapshots each; the command used the ephemeral migrated database and no LLM.

Phase 2 migration, seed, complete repository, and immutability verification
remain covered by the same backend suite. No schema change was needed in Phase
3, so migration revision `5bd72efdd0ea` remains current.

## Known limitations

- Profile/scenario/universe domain APIs remain deferred to Phase 5; the only API
  route is still the health endpoint.
- The frontend remains the Phase 1 foundation screen and does not expose seeded
  persistence yet.
- Narrative providers, generated artifacts, and future-self behavior remain
  deferred to their specified phases. Phase 3 system event text is fixed engine
  configuration and does not implement the Phase 4 narrative abstraction.
- Yearly summaries are returned as mechanical engine results but are not yet
  exposed through an API or persisted as narrative content.
- `make reset-db` intentionally destroys existing local simulation data before
  restoring the demo seed.
- pnpm continues to report that it blocks the optional `unrs-resolver`
  lifecycle script; current tests and builds do not require it.

## Next task

Phase 4 — Mock narrative system, only when explicitly requested.
