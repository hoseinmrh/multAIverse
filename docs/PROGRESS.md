# Progress

## Current phase

Phase 2 — Domain and persistence: **complete** (2026-08-01)

## Completed work

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

## Verification

All final checks passed:

- `make setup` — passed with frozen `uv.lock` and `pnpm-lock.yaml`.
- Clean database `alembic upgrade head` — applied revision `5bd72efdd0ea`.
- Clean database `scripts/seed_demo.py` — created 1 profile, 1 scenario, 3
  universes, and 3 initial snapshots.
- `alembic current` — reported `5bd72efdd0ea (head)`.
- `alembic check` — reported no new upgrade operations.
- `make reset-db` — downgraded to base, upgraded to head, and restored the demo.
- `make seed` — passed and remained idempotent.
- `make test` — 10 backend tests and 2 frontend tests passed.
- `make lint` — Ruff and ESLint passed with no findings.
- `make format-check` — Ruff and Prettier checks passed.
- `make typecheck` — strict MyPy and TypeScript checks passed.
- `make build` — backend/app/migration/script byte-compilation and the Next.js
  16.2.12 production build passed; `/` was statically generated.

The first sandboxed pnpm setup attempt could not access the package registry,
and the sandboxed Turbopack build could not bind its private worker port. The
frozen install and unchanged build both passed with normal local permissions;
these were verification-environment restrictions rather than code failures.

## Known limitations

- The deterministic simulation engine has not begun. No time advancement,
  effect application, seeded event selection, or choice resolution exists yet.
- Profile/scenario/universe domain APIs remain deferred to Phase 5; the only API
  route is still the health endpoint.
- The frontend remains the Phase 1 foundation screen and does not expose seeded
  persistence yet.
- Narrative providers, generated artifacts, and future-self behavior remain
  deferred to their specified phases. Phase 2 persists their domain records but
  does not generate content.
- `make reset-db` intentionally destroys existing local simulation data before
  restoring the demo seed.
- pnpm continues to report that it blocks the optional `unrs-resolver`
  lifecycle script; current tests and builds do not require it.

## Next task

Phase 3 — Deterministic simulation engine, only when explicitly requested.
