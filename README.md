# Multiverse

Multiverse is a local-first fictional alternate-life simulator. The project is
currently at **Phase 2: Domain and persistence**: the FastAPI backend, Next.js
foundation, SQLite domain schema, migrations, and seeded demo data are
operational. The deterministic simulation engine begins in Phase 3.

> Multiverse creates fictional scenarios for entertainment and reflection. Its
> simulations are not predictions or professional advice.

## Prerequisites

- Node.js 20.9 or newer (the repository pins 24.10.0 for local development)
- pnpm 10.33.0
- `uv`
- GNU Make

On macOS, install the missing Python tooling with:

```bash
brew install uv
uv python install 3.12
```

`uv` uses `.python-version` and manages the virtual environment automatically.

## Setup

```bash
cp .env.example .env
make setup
make seed
```

No API key is needed. `OPENAI_API_KEY` is intentionally unused until the
OpenAI narrative-provider phase.

## Run locally

Start both applications:

```bash
make dev
```

Then open <http://localhost:3000>. The API health endpoint is available at
<http://127.0.0.1:8000/api/v1/health>, and interactive API documentation is at
<http://127.0.0.1:8000/docs>.

To run the processes separately:

```bash
make backend-dev
make frontend-dev
```

## Quality commands

```bash
make test
make lint
make format-check
make typecheck
make build
```

`make format` applies Ruff and Prettier formatting. `make seed` applies pending
Alembic migrations and idempotently creates the demo profile, scenario, three
universes, and their initial snapshots. `make reset-db` destructively rebuilds
the local database and restores that seed.

Direct migration commands can be run from `backend/`:

```bash
uv run alembic upgrade head
uv run alembic current
uv run alembic check
```

## Configuration

Backend settings are read from environment variables or the root `.env` file.
Only variables beginning with `NEXT_PUBLIC_` are available to browser code.
Never add secrets to those variables.

If the ports change, update both `BACKEND_PORT` and
`NEXT_PUBLIC_API_BASE_URL`. Add the frontend origin to
`BACKEND_CORS_ORIGINS` when changing its port or hostname.

## Troubleshooting

- **`uv` cannot find Python 3.12:** run `uv python install 3.12`.
- **The frontend says the backend is unavailable:** start `make backend-dev`
  and verify the URL configured by `NEXT_PUBLIC_API_BASE_URL`.
- **Port 3000 or 8000 is occupied:** stop the conflicting process or run each
  application separately with an alternate port and matching environment values.
- **Dependency state is stale:** remove only the generated `.venv`,
  `node_modules`, and `.next` directories, then run `make setup` again.
- **The database schema is missing:** run `make seed` to migrate and populate it.
- **A local database needs a clean rebuild:** run `make reset-db`. This removes
  existing local simulation data before restoring the demo seed.

See [the architecture overview](docs/ARCHITECTURE.md),
[implementation plan](docs/PLAN.md), and [progress log](docs/PROGRESS.md).
