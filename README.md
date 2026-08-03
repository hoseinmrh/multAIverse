# Multiverse

Multiverse is a local-first fictional alternate-life simulator. The project has
completed **Phase 6: Core frontend MVP**. The polished Next.js application now
drives the FastAPI APIs for profile onboarding, scenario generation, a React
Flow multiverse map, yearly decisions, immutable timelines, statistics,
artifacts, comparison charts, future-self chat, settings, and demo reset. The
offline mock narrative provider powers the entire experience without an API
key.

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

No API key or network connection is needed. The offline mock provider powers
the complete backend flow. `OPENAI_API_KEY` is intentionally unused until the
OpenAI narrative-provider phase.

To run all three seeded universes through five deterministic years in an
ephemeral database, without an LLM or narrative provider:

```bash
make simulation-demo
```

The command prints the final 2031 statistics and leaves the normal local
database unchanged.

## Run locally

Start both applications:

```bash
make dev
```

Then open <http://localhost:3000>. The API health endpoint is available at
<http://127.0.0.1:8000/api/v1/health>, and interactive API documentation is at
<http://127.0.0.1:8000/docs>.

From the landing page, choose **Explore Hosein's demo** to open the seeded three-
branch map. Open any universe, advance a year, resolve its decision, inspect the
updated statistics, timeline, and artifact, then use **Compare universes** and
**Talk to future self**. **Enter the Multiverse** starts the seven-step profile
and scenario creation flow. Settings reports the active provider, stores local
motion/default preferences, and can restore all three demo universes to 2026.

The main frontend routes are:

- `/` — landing and demo entry
- `/onboarding` and `/scenario` — profile and scenario creation
- `/multiverse/{scenario_id}` — interactive universe graph
- `/universe/{universe_id}` — yearly simulation, statistics, timeline, choices,
  and artifacts
- `/compare/{scenario_id}` — accessible comparison charts and data tables
- `/future-self/{universe_id}` — grounded fictional future-self conversation
- `/settings` — provider, preferences, version, disclaimer, and demo reset

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

Backend-only Phase 5 verification can be run from `backend/` with
`uv run pytest`, `uv run ruff check app tests migrations ../scripts`, and
`uv run mypy app tests ../scripts`.

Frontend-only verification can be run with:

```bash
pnpm --dir frontend format:check
pnpm --dir frontend lint
pnpm --dir frontend typecheck
pnpm --dir frontend test
pnpm --dir frontend build
```

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

`GET /api/v1/config/public` exposes only safe UI configuration and never
returns database settings or credentials. Profile data remains local in mock
mode. A future OpenAI provider may send the bounded narrative context described
in `docs/ARCHITECTURE.md`; it is not implemented or active yet.

If the ports change, update both `BACKEND_PORT` and
`NEXT_PUBLIC_API_BASE_URL`. Add the frontend origin to
`BACKEND_CORS_ORIGINS` when changing its port or hostname.

## Troubleshooting

- **`uv` cannot find Python 3.12:** run `uv python install 3.12`.
- **The frontend says the backend is unavailable:** start `make backend-dev`
  and verify the URL configured by `NEXT_PUBLIC_API_BASE_URL`.
- **The map loads without yearly nodes:** this is the expected empty state for
  a newly seeded universe; open it and advance a year.
- **A universe cannot advance:** open its pending decision and select one of the
  server-provided choices before trying again.
- **Port 3000 or 8000 is occupied:** stop the conflicting process or run each
  application separately with an alternate port and matching environment values.
- **Dependency state is stale:** remove only the generated `.venv`,
  `node_modules`, and `.next` directories, then run `make setup` again.
- **The database schema is missing:** run `make seed` to migrate and populate it.
- **A local database needs a clean rebuild:** run `make reset-db`. This removes
  existing local simulation data before restoring the demo seed.

See [the architecture overview](docs/ARCHITECTURE.md),
[implementation plan](docs/PLAN.md), and [progress log](docs/PROGRESS.md).
