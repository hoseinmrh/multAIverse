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
  ├── deterministic engine
  ├── narrative-provider port
  │     └── offline seeded mock adapter
  └── repositories → SQLAlchemy → SQLite
```

The browser never receives backend credentials. The backend is the source of
truth for API contracts, state changes, and persistence. The
frontend treats it as an HTTP service rather than importing backend code.

## Implemented frontend

- `frontend/app` contains the Next.js App Router routes for landing, onboarding,
  scenario creation, the multiverse map, universe detail, comparison,
  future-self chat, and settings.
- `frontend/lib/api` is the only browser HTTP boundary. It owns the base URL,
  error normalization, request functions, and Zod validation for every response
  the UI consumes. Components do not scatter raw `fetch` calls.
- TanStack Query owns server state. Stable query keys cover scenario, universe
  state, timeline, events, artifacts, comparison, config, profiles, and
  conversations. Mutations invalidate every affected view after generation,
  advancement, choice resolution, reset, and messaging.
- Feature components remain grouped by onboarding, scenarios, universes,
  artifacts, comparison, and future self. They consume typed client values and
  never calculate or persist simulation outcomes.
- React Flow renders the central reality, three universe branches, and yearly
  event chains. Recharts renders comparison trends; hidden semantic tables keep
  the same data available without relying on the chart canvas.
- Framer Motion is limited to restrained transitions. A stored preference and
  `prefers-reduced-motion` both suppress decorative motion. Skip links, visible
  focus styles, semantic meters, keyboard-reachable nodes, a trapped decision
  dialog, and labeled chart data support keyboard and assistive-technology use.
- `backend/app/main.py` creates the FastAPI application and local CORS policy.
- `backend/app/api/v1` owns the complete Phase 5 versioned route surface.
- `backend/app/services/application.py` coordinates API use cases and owns
  their transaction boundaries. Route functions contain no domain decisions.
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
- `backend/app/schemas` provides strict Pydantic input/read and API response
  contracts. Generated narrative and effect schemas live beside their owning
  services.
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
  → schema-validated significant narrative event
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

Mechanical routine events remain engine fixtures. API advancement replaces the
engine's significant-event fixture with a provider proposal while retaining
the same deterministic preparation, validation, caps, and finalization.

## Phase 4 narrative system

`backend/app/services/narrative` is a provider boundary with four parts:

- `provider.py` defines the asynchronous, runtime-checkable
  `NarrativeProvider` protocol.
- `schemas.py` defines closed Pydantic contracts for branch, event, choice,
  yearly-summary, structured-artifact, future-self-profile, and future-self
  reply content. Proposed effects reuse the deterministic engine's schemas.
- `context.py` builds a bounded, immutable context from values the application
  has already loaded: a concise profile and universe summary, current state,
  important flags, three recent major events, duplicate-prevention keys,
  unresolved decisions, long-term summary, mode, year, and effect allowlist.
- `mock.py` implements an offline template provider with namespaced seeded
  selection for all three demo paths. State and mode affect selection, and
  consumed event keys are excluded.

The dependency direction is one-way:

```text
application-loaded domain values
        ↓
NarrativeContextBuilder → immutable NarrativeContext
        ↓
NarrativeProvider → schema-validated proposals only
        ↓
deterministic engine validates/caps/applies effects
        ↓
application service persists the complete result atomically
```

Providers have no SQLAlchemy session or repository dependency. They cannot
commit, write artifacts/events, update a universe, mutate a snapshot, schedule
delayed effects, or call state-transition functions. The context builder does
no querying; callers pass already-loaded objects.

The mock provider uses the universe seed plus stable namespaces such as year,
mode, operation, event key, and prior keys. Repeating the same context produces
the same branch, event, artifact, personality, and reply. It does not read an
API key and makes no network request.

Structured artifacts cover the six initial contracts: news article, academic
abstract, company announcement, diary entry, email, and social/professional
post. Every artifact carries `is_fictional=true` metadata and uses fictional
organizations and supporting characters.

`make mock-narrative-demo` composes the mock provider with the pure engine for
five years in each seeded universe. The engine validates, caps, and applies
chosen proposals; the harness also creates summaries, artifacts, and a
future-self exchange.

## Phase 5 core API and application services

All public routes are under `/api/v1`. The route modules are split by profiles,
scenarios, universes, events/choices, artifacts, future self, and system
configuration. They parse typed inputs, call `CoreApplicationService`, and
return typed responses; persistence queries and decisions stay out of handlers.

```text
FastAPI route
  → request-scoped CoreApplicationService
      → repositories load domain state
      → bounded NarrativeContextBuilder
      → mock provider returns validated proposal
      → SimulationService + deterministic engine validate/apply
      → repositories flush events/snapshots/artifacts/messages
  → transaction commit
  → explicit Pydantic response
```

Universe generation validates the complete branch set before creating the
universes and their initial snapshots in one transaction. Annual advancement
persists a pending significant event without a snapshot when user input is
required. Choice resolution deterministically regenerates the event, checks its
persisted narrative key, applies the selected effects once, schedules delayed
effects, creates the summary and artifact, and appends the final snapshot in a
single transaction. A provider or persistence exception rolls back all of it.

The selected-choice uniqueness constraint provides a database backstop for
idempotency. The service handles an identical repeat by returning the existing
state and rejects a conflicting selection. Unresolved choices keep the universe
blocked.

Reset deletes all derived history after the initial immutable snapshot within
one transaction. Comparison is read-only and exposes named wellbeing,
sustainability, career, research, and financial components without collapsing
the result into one best-universe score.

Future-self creation stores the generated personality summary on the
conversation. Subsequent identity cards are rebuilt from current persisted
state but reuse that stored personality. Message generation happens before the
user/reply pair is flushed, preventing half conversations.

Growing profile, scenario, timeline, event, artifact, and message collections
use SQL `OFFSET`/`LIMIT` plus a total count. Validation and runtime failures use
one safe error envelope that does not echo submitted values or expose secrets.

Alembic revision `8f4d3b2a1c0e` adds the narrative replay key to events and the
stable personality summary to future-self conversations.

## Phase 6 frontend request flows

```text
landing demo action
  → scenario detail query
  → React Flow map
  → universe detail queries (state + timeline + events + artifacts)
  → POST advance
       ├── automatic result → invalidate all universe/comparison queries
       └── blocked result → decision dialog
              → POST choice selection
              → invalidate state/timeline/events/artifacts/map/comparison
```

Profile onboarding validates a complete `PersonProfileCreate` locally with Zod
before `POST /profiles`. Scenario creation validates its input, calls
`POST /scenarios`, then calls the idempotent universe-generation endpoint before
navigating to the new map. Optional planning-horizon and direction notes are
stored in the scenario description because the Phase 5 contract deliberately
has no frontend-only simulation fields.

Future-self entry creates a persisted conversation. Sending a message updates
the query cache from the atomic backend response and then revalidates the
conversation. Reset calls the backend reset endpoint and invalidates all cached
views; no client-only snapshot, event, artifact, or chat data is fabricated.

Artifact content is always rendered as text through type-specific React layouts
and never injected as HTML. Provider configuration comes only from
`GET /config/public`; credentials have no frontend representation.

## Remaining boundaries

SQLAlchemy models represent storage only. Repositories receive a session and
never decide simulation outcomes. The deterministic simulation engine accepts
immutable typed values and returns new values without importing FastAPI or
SQLAlchemy.

The OpenAI adapter is intentionally deferred to Phase 8. `mock` is the only
narrative configuration in the current phase, ensuring offline use remains the
complete default path. Historical universe forking also remains deferred because
the Phase 5 backend does not expose a fork route; the detail screen labels that
control as unavailable instead of simulating a fork in browser state.

SQLite is the MVP store. Alembic will be the only schema-management path. The
local web boundary remains compatible with a future Tauri shell without adding
desktop concerns to the MVP.
