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
  ├── deterministic engine       (Phase 3)
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
  narrative schemas and effect validation remain intentionally deferred.
- Session-scoped repositories flush changes but never commit. Application
  services, beginning with the demo seed service, own transaction boundaries.
- Snapshot persistence is append-only through its repository, and SQLAlchemy
  rejects updates to an existing snapshot.
- Alembic is the only production schema creation path. Application startup does
  not create tables.

The idempotent demo seed uses stable UUIDs and deterministic integer seeds. It
creates one profile, one scenario, three universe definitions, and an initial
2026 snapshot for each universe.

## Planned boundaries

SQLAlchemy models represent storage only. Repositories receive a session and
never decide simulation outcomes. The deterministic simulation engine will
accept immutable typed values and return new values without importing FastAPI
or SQLAlchemy.

Narrative providers will be replaceable backend-only adapters. They may
propose schema-validated content but may not write to the database or mutate
simulation state.

SQLite is the MVP store. Alembic will be the only schema-management path. The
local web boundary remains compatible with a future Tauri shell without adding
desktop concerns to the MVP.
