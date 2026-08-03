# Multiverse

Multiverse is a local-first fictional alternate-life simulator. The project has
completed the core frontend and optional OpenAI narrative-provider phases. The
polished Next.js application now
drives the FastAPI APIs for profile onboarding, scenario generation, a React
Flow multiverse map, yearly decisions, immutable timelines, statistics,
artifacts, comparison charts, future-self chat, a saved-story library, settings,
and demo reset. The
offline mock narrative provider remains the default and powers the entire
experience without an API key. An optional backend-only OpenAI Responses API
adapter adds schema-constrained narrative generation when explicitly enabled.

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
the complete backend flow.

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
that supports Structured Outputs. For current GPT-5.6 models,
`gpt-5.6-luna` is the lowest-cost recommendation for these tightly structured
tasks; use `gpt-5.6-terra` when richer prose is worth the additional cost. Avoid
the bare `gpt-5.6` alias for routine generation because it selects the frontier
Sol tier. There is deliberately no hardcoded model default.

For GPT-5 models, `OPENAI_REASONING_EFFORT=low` is the economical starting
point. Leave `OPENAI_VERBOSITY` unset for `gpt-5.6-luna`; its Responses API
currently rejects that optional control. Omit either variable for any model
that does not support it, and increase reasoning to `medium` only after a local
quality comparison demonstrates a benefit. If OpenAI reports an optional
control as unsupported, the adapter retries once within the configured retry
budget with both optional controls omitted. Requests use the Responses API
with Pydantic Structured Outputs, `store=false`, a bounded timeout, task-specific
800-3,000 token output ceilings, and at most `OPENAI_MAX_RETRIES + 1` total
attempts. Authentication errors are not retried. When fallback is enabled,
provider failures use the deterministic mock implementation; incomplete OpenAI
configuration also activates the mock fallback. The Settings screen reports
configured, fallback, or unavailable state without exposing a credential.

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
- **OpenAI status shows fallback:** set both backend-only `OPENAI_API_KEY` and
  `OPENAI_MODEL`, or return to `NARRATIVE_PROVIDER=mock`. Check that the chosen
  model supports Responses API Structured Outputs.
- **OpenAI status shows unavailable:** enable `OPENAI_FALLBACK_TO_MOCK=true` to
  keep narrative tasks playable while correcting backend configuration.
- **A local database needs a clean rebuild:** run `make reset-db`. This removes
  existing local simulation data before restoring the demo seed.

See [the architecture overview](docs/ARCHITECTURE.md),
[implementation plan](docs/PLAN.md), and [progress log](docs/PROGRESS.md).
