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
  ├── application services       (later phases)
  ├── deterministic engine       (Phase 3)
  ├── narrative-provider port    (Phase 4)
  └── repositories → SQLite      (Phase 2)
```

The browser never receives backend credentials. The backend is the future
source of truth for API contracts, state changes, and persistence. The
frontend treats it as an HTTP service rather than importing backend code.

## Phase 1 implementation

- `frontend/app` contains the Next.js App Router shell.
- `frontend/components/backend-status.tsx` makes a browser-side request to the
  health endpoint and presents checking, online, and unavailable states.
- `backend/app/main.py` creates the FastAPI application and local CORS policy.
- `backend/app/api/v1` owns versioned routes. Only `/health` exists in Phase 1.
- Environment configuration is centralized in `backend/app/core/config.py`.

## Planned boundaries

SQLAlchemy models will represent storage only. Repositories receive a session
and never decide simulation outcomes. Application services will own commits.
The deterministic simulation engine will accept immutable typed values and
return new values without importing FastAPI or SQLAlchemy.

Narrative providers will be replaceable backend-only adapters. They may
propose schema-validated content but may not write to the database or mutate
simulation state.

SQLite is the MVP store. Alembic will be the only schema-management path. The
local web boundary remains compatible with a future Tauri shell without adding
desktop concerns to the MVP.
