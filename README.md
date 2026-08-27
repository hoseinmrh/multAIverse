# Multiverse

[![CI](https://github.com/hoseinmrh/multAIverse/actions/workflows/ci.yml/badge.svg)](https://github.com/hoseinmrh/multAIverse/actions/workflows/ci.yml)

Multiverse is a local-first fictional alternate-life simulation game. Create a
profile, branch one major decision into three possible futures, advance their
timelines, resolve trade-offs, compare outcomes, inspect fictional artifacts,
and talk to a generated future self.

The Next.js frontend uses the versioned FastAPI API; SQLite stores local data,
and a deterministic engine owns every state change. The offline mock narrative
provider is the default and supports the complete experience without an API
key. An optional backend-only OpenAI Responses API provider adds
schema-constrained narrative generation when explicitly configured.

> Multiverse creates fictional scenarios for entertainment and reflection. Its
> simulations are not predictions or professional advice.

## Prerequisites

- Git
- Node.js 20.9 or newer (the repository and CI pin 24.10.0)
- pnpm 10.33.0
- `uv` with access to Python 3.12+
- Bash and GNU Make

On macOS, one installation option is:

```bash
brew install node uv
npm install --global pnpm@10.33.0
uv python install 3.12
```

On Linux or Windows, install [Node.js](https://nodejs.org/en/download) and
[pnpm](https://pnpm.io/installation) through their official installers and
install `uv` using its
[platform instructions](https://docs.astral.sh/uv/getting-started/installation/).
Windows contributors should use WSL because the shared development commands are
Bash/Make based. `uv` reads `.python-version` and manages the backend virtual
environment automatically.

## Quick start

Clone the repository and enter it:

```bash
git clone https://github.com/hoseinmrh/multAIverse.git
cd multAIverse
```

Create local configuration, install the locked dependencies, and seed the demo:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
make setup
make seed
```

First-time dependency and tool installation needs network access. After those
dependencies are installed, the default mock experience needs no API key or
external narrative service.

Start both applications:

```bash
make dev
```

Open <http://localhost:3000>. The API health endpoint is
<http://127.0.0.1:8000/api/v1/health>, and interactive API documentation is at
<http://127.0.0.1:8000/docs>. Stop both processes with `Ctrl+C`.

The seed command applies all Alembic migrations, creates
`backend/data/multiverse.db`, and idempotently adds the demo profile, scenario,
three universes, and initial snapshots. Re-running `make seed` is safe.

To run all three seeded universes through five deterministic years in an
ephemeral database, without an LLM or narrative provider:

```bash
make simulation-demo
```

The command prints the final 2031 statistics and leaves the normal local
database unchanged.

## Explore the demo

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

GitHub Actions runs the same backend and frontend tests, linting, formatting,
strict type checks, migration drift check, and production build on pushes to
`main` and on pull requests. Dependabot checks the pnpm, uv, and GitHub Actions
dependencies weekly.

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
The frontend reads its browser-safe configuration from `frontend/.env.local`.
Only variables beginning with `NEXT_PUBLIC_` are available to browser code;
never add credentials or other secrets to the frontend environment file.

`GET /api/v1/config/public` exposes only safe UI configuration and provider
readiness; it never returns database settings or credentials. Profile data
remains local in mock mode.

The default provider configuration is:

```env
NARRATIVE_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_MODEL=
OPENAI_TIMEOUT_SECONDS=30
OPENAI_MAX_RETRIES=2
OPENAI_FALLBACK_TO_MOCK=true
# OPENAI_REASONING_EFFORT=low
# OPENAI_VERBOSITY=low
```

To enable OpenAI generation, set `NARRATIVE_PROVIDER=openai`, provide a
backend-only `OPENAI_API_KEY`, and set `OPENAI_MODEL` to a Responses API model
that supports Structured Outputs. OpenAI's current
[model guidance](https://developers.openai.com/api/docs/guides/latest-model)
positions `gpt-5.6-luna` for efficient high-volume work and `gpt-5.6-terra` for
a balance of intelligence and cost; evaluate both on representative narrative
tasks. The bare `gpt-5.6` alias routes to the frontier Sol tier. There is
deliberately no hardcoded model default.

Leave `OPENAI_REASONING_EFFORT` and `OPENAI_VERBOSITY` unset initially to use
the selected model's defaults. Add supported controls only after comparing
quality, latency, and cost on this application's structured tasks. If OpenAI
reports an optional control as unsupported, the adapter retries once within the
configured retry budget with both optional controls omitted. Requests use the
Responses API with Pydantic Structured Outputs, `store=false`, a bounded
timeout, task-specific 800-3,000 token output ceilings, and at most
`OPENAI_MAX_RETRIES + 1` total attempts. Authentication errors are not retried.
When fallback is enabled, provider failures use the deterministic mock
implementation; incomplete OpenAI configuration also activates the mock
fallback. The Settings screen reports configured, fallback, or unavailable
state without exposing a credential.

Set `OPENAI_FALLBACK_TO_MOCK=false` for GPT-only narrative mode. In that mode,
universe branches and initial states, yearly decision scenarios and choices,
timeline prose, summaries, artifacts, and future-self content must all pass
through OpenAI structured outputs. A provider failure returns an error and the
transaction preserves the current simulation state. Deterministic code still
validates/caps proposed effects, applies finances and delayed consequences, and
owns immutable state transitions; those safety mechanics are not delegated to
the model.

### Information sent to OpenAI

OpenAI receives data only when `NARRATIVE_PROVIDER=openai` is fully configured
and a narrative task runs. Each request is capped at 20,000 characters. Stable,
compact instructions and task-specific payloads avoid repeatedly sending fields
that cannot help the requested output:

- Profile name and current age; starting location and occupation; education;
  at most 800 biography characters; up to five strengths and interests; and up
  to four goals and constraints. Birth year and growth edges/weaknesses are not
  sent.
- Universe name, slug, premise, starting direction, deterministic seed,
  simulation mode, and current year.
- Current stored location, career, income, net worth, normalized statistics,
  skills, and active flags.
- Timeline tasks receive at most the last three major events, three unresolved
  decisions, and a long-term summary capped at 1,500 characters.
- Significant-event generation additionally receives at most 40 compact
  duplicate-prevention event keys and the explicit effect-field allowlist.
  Those fields are omitted from summaries, artifacts, future-self profiles, and
  replies.
- Artifacts and summaries receive the relevant event's identity, prose,
  category, importance, artifact suggestions, and tags. Proposed choices and
  effect payloads are omitted because the completed stored state is authoritative.
- For future-self chat, the stored future-self identity/personality, the new
  user message, and only the eight most recent conversation messages. Replies
  may reference only event keys present in the stored timeline.

The API key itself is used only by the backend SDK and is never included in
prompts, logs, URLs, browser bundles, or API responses. Model outputs are
validated against closed Pydantic schemas; proposed effects still pass through
the deterministic engine before persistence. Provider failures occur inside
application transaction boundaries, so unfinished simulation changes are
rolled back.

To use different local ports, update `NEXT_PUBLIC_API_BASE_URL` in
`frontend/.env.local` and `BACKEND_CORS_ORIGINS` in the root `.env`, then launch
with matching Make parameters. For example:

```bash
make dev BACKEND_PORT=8001 FRONTEND_PORT=3001
```

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
- **`pnpm` is missing or has the wrong version:** run
  `npm install --global pnpm@10.33.0`, then confirm with `pnpm --version`.
- **Make commands fail on Windows:** run the project inside WSL; native Windows
  shells are not currently supported by the shared Bash scripts.
- **The database schema is missing:** run `make seed` to migrate and populate it.
- **OpenAI status shows fallback:** set both backend-only `OPENAI_API_KEY` and
  `OPENAI_MODEL`, or return to `NARRATIVE_PROVIDER=mock`. Check that the chosen
  model supports Responses API Structured Outputs.
- **OpenAI status shows unavailable:** enable `OPENAI_FALLBACK_TO_MOCK=true` to
  keep narrative tasks playable while correcting backend configuration.
- **A local database needs a clean rebuild:** run `make reset-db`. This removes
  existing local simulation data before restoring the demo seed.

See [the architecture overview](docs/ARCHITECTURE.md),
[implementation plan](docs/PLAN.md), [progress log](docs/PROGRESS.md), and
[contribution guide](CONTRIBUTING.md). Repository owners should also complete
the post-push [GitHub settings checklist](docs/GITHUB_SETUP.md). Report suspected
vulnerabilities through the private process in [SECURITY.md](SECURITY.md).

## Project status

The core mock and optional OpenAI flows, backend API, frontend screens, and
automated unit/integration checks are implemented. Phase 9 remains in progress:
the repository does not yet contain the product spec's Playwright browser happy
path, historical universe forking remains unavailable, and a full interactive
accessibility/responsive walkthrough is still pending. See
[`docs/PROGRESS.md`](docs/PROGRESS.md) for the exact verification history and
known limitations.
