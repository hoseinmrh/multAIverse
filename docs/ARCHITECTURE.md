# Architecture

## System boundary

```text
Browser
  │ HTTP/JSON
  ▼
Next.js frontend :3000
  │ /api/v1 requests
  ▼
FastAPI backend :8000
  ├── API routes
  ├── application services       (transaction boundaries)
  ├── deterministic engine       (implemented in Phase 3)
  ├── narrative-provider port    (Phase 4)
  └── repositories → SQLAlchemy → SQLite
```

The browser never receives backend credentials. The backend is the future
source of truth for API contracts, state changes, and persistence. The
frontend treats it as an HTTP service rather than importing backend code.

## Implemented foundation

- `frontend/app` contains the Next.js App Router shell.
- `frontend/components/backend-status.tsx` makes a browser-side request to the
  health endpoint and presents checking, online, and unavailable states.
- `backend/app/main.py` creates the FastAPI application and local CORS policy.
- `backend/app/api/v1` owns versioned routes. Only `/health` exists in Phase 1.
- Environment configuration is centralized in `backend/app/core/config.py`.

## Phase 2 persistence

- `backend/app/models` contains storage entities for profiles, scenarios,
  universes, immutable life-state snapshots, events, choices, delayed effects,
  artifacts, and future-self conversations/messages.
- Scalar domain state is stored in normalized columns. JSON is limited to
  naturally variable collections and payloads such as interests, effects,
  skills, flags, themes, and type-specific artifact content/metadata.
- Foreign keys, enum checks, normalized-stat checks, aggregate uniqueness, and
  one-selected-choice-per-event constraints are enforced by the database.
- `backend/app/schemas` provides strict Pydantic input/read contracts. Generated
  narrative schemas remain deferred; Phase 3 effect validation lives beside the
  engine in `backend/app/services/simulation/schemas.py`.
- Session-scoped repositories flush changes but never commit. Application
  services, beginning with the demo seed service, own transaction boundaries.
- Snapshot persistence is append-only through its repository, and SQLAlchemy
  rejects updates to an existing snapshot.
- Alembic is the only production schema creation path. Application startup does
  not create tables.

The idempotent demo seed uses stable UUIDs and deterministic integer seeds. It
creates one profile, one scenario, three universe definitions, and an initial
2026 snapshot for each universe.

## Phase 3 deterministic engine

`backend/app/services/simulation` is split by responsibility:

- `balance.py` is the source of truth for score limits, annual caps, stress and
  burnout thresholds, happiness weights, financial rates, momentum weights,
  mode modifiers, and progression tuning.
- `schemas.py` strictly validates immediate effects, delayed-effect envelopes,
  finance changes, flags, skills, and choice requirements. Unknown statistics
  and extra fields are rejected before state application.
- `randomness.py` derives stable SHA-256 sub-seeds and creates local
  `random.Random` instances. No global random state is used.
- `state.py` owns the deeply immutable `SimulationState` and pure clamping,
  diminishing-return, effect, requirements, happiness, burnout, momentum, and
  finance calculations.
- `events.py` contains deterministic system-event and choice configuration.
  These are engine fixtures, not generated narrative and not a narrative
  provider.
- `engine.py` prepares and finalizes pure yearly transitions.
- `service.py` is the SQLAlchemy adapter and transaction boundary. It is the
  only simulation component that persists events, delayed effects, universe
  cursors, or snapshots.

The deterministic identity for a random draw is derived from the universe
seed plus stable context such as year, subsystem, path, and delayed-effect
content. Database UUIDs and process hash randomization never influence an
outcome. Repeating a simulation with the same seed and choices therefore
produces the same state history.

### Annual transition and unresolved choices

```text
latest immutable snapshot
  → due delayed effects (seeded probability)
  → baseline stress/health flags
  → career/research/startup momentum
  → seeded path outcome
  → income, savings, assets/debt
  → routine system event
  → significant system event
       ├── automatic: effects → happiness → append snapshot
       └── decision: persist choices → mark universe blocked
                                      ↓
                         selected valid choice (exactly once)
                                      ↓
                    immediate effects + schedule delayed effects
                                      ↓
                         happiness → append snapshot → active
```

A choice year is intentionally two-step. Advancement persists the pending
decision but does not create that year's snapshot. Choice resolution reruns
the deterministic year plan, validates requirements/effects, applies the
selection, and atomically appends the snapshot. This respects the database's
one-snapshot-per-year and append-only guarantees. Re-selecting the same choice
returns the existing final state; selecting a different choice after resolution
is rejected.

No narrative provider, artifact generator, or LLM participates in Phase 3.
Mechanical event descriptions and yearly summaries exist only to make engine
results inspectable. Phase 4 will add the narrative port without granting it
state or persistence authority.

## Planned boundaries

SQLAlchemy models represent storage only. Repositories receive a session and
never decide simulation outcomes. The deterministic simulation engine accepts
immutable typed values and returns new values without importing FastAPI or
SQLAlchemy.

Narrative providers will be replaceable backend-only adapters. They may
propose schema-validated content but may not write to the database or mutate
simulation state.

SQLite is the MVP store. Alembic will be the only schema-management path. The
local web boundary remains compatible with a future Tauri shell without adding
desktop concerns to the MVP.
