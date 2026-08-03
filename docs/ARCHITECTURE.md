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
  │     ├── offline seeded mock adapter (default)
  │     └── OpenAI Responses API adapter (optional, backend-only)
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

Mechanical routine effects remain engine-owned fixtures. API advancement
replaces the engine's significant-event fixture with a provider proposal while
retaining deterministic preparation, validation, caps, and finalization. After
the state is finalized, the provider's validated yearly summary replaces the
routine event's visible title and description before the transaction commits;
the deterministic routine prose is therefore not exposed as story content.

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

## Optional OpenAI narrative provider

`OpenAINarrativeProvider` implements the same persistence-free protocol through
the asynchronous OpenAI Responses API. Every narrative operation has its own
prompt builder: universe branches, significant events, yearly summaries,
artifacts, future-self profiles, and future-self replies. The adapter calls
`responses.parse` with the existing Pydantic output model, disables response
storage, caps serialized output size, and validates the parsed object again
before returning it. Output ceilings are task-specific: short future-self
answers and profiles receive smaller budgets than events and three-branch
generation. Optional reasoning-effort and verbosity controls let GPT-5 models
run economically without forcing unsupported parameters onto other models.
Dynamic engine maps (skills, stat effects, and requirements) use bounded unique
`{key,value}` entries only on the Structured Outputs wire, because strict JSON
schemas reject dynamically keyed objects. Pydantic converts them back into the
existing validated dictionaries before any proposal reaches the engine.

```text
bounded application values
  → task-specific prompt builder (20,000-character request ceiling)
  → Responses API + Pydantic Structured Output (store=false)
  → semantic checks (year, event key, artifact link, identity grounding)
  → deterministic engine validation/capping
  → one application-owned transaction commit
```

The SDK's automatic retries are disabled. The adapter owns a zero-to-five
retry budget from `OPENAI_MAX_RETRIES`, applies a short bounded backoff to
timeouts, connection failures, rate limits, invalid structured output, and
empty responses, and never retries authentication failures. Logs contain only
operation name, attempt number, safe error category, HTTP status, and fallback
state—never exception messages, response bodies, prompts, profile content, or
credentials. A model-specific `unsupported_parameter` response for optional
reasoning or verbosity controls consumes at most one configured retry and
resends the request with those controls omitted. With
`OPENAI_FALLBACK_TO_MOCK=true`, exhausted or non-retryable provider errors run
the same operation through `MockNarrativeProvider`.

With `OPENAI_FALLBACK_TO_MOCK=false`, OpenAI mode is narrative-strict: branch
premises and initial states, yearly significant events and choices, routine
timeline prose, summaries, artifacts, future-self profiles, and replies all
come from validated OpenAI outputs. An untouched mock-authored universe set is
transactionally regenerated and tagged with provider provenance when opened;
played snapshots and resolved decisions are immutable and are never rewritten.

OpenAI-generated decisions are not regenerated when a user later selects a
choice. Their strictly validated choices and effects are persisted with the
pending event, then reconstructed from that stored proposal for deterministic
resolution. This avoids relying on nondeterministic model replay and ensures
the engine applies exactly the proposal the user saw. Summary or artifact
failure after resolution still rolls back the surrounding transaction.

Provider status is derived without probing the external API. Public config
reports the requested provider, active configured/fallback provider, model,
fallback flag, and safe readiness detail. It has no credential field. Runtime
provider errors remain user-safe `503 narrative_unavailable` responses when no
fallback succeeds.

The data disclosed when OpenAI mode is active is intentionally bounded and
task-specific: profile name/current age, starting location/occupation,
education, shortened biography, limited strengths/interests/goals/constraints,
universe premise/direction/seed, current stored state and flags, three recent
major events, up to three unresolved decisions, a 1,500-character long-term
summary, and mode/year. Only significant-event generation receives the 40-key
duplicate-prevention window and effect allowlist. Summaries and artifacts
receive a compact event record without proposed choice/effect payloads.
Future-self replies additionally include the persisted identity/personality,
current message, and eight recent chat messages. Birth year and profile
weaknesses are not sent. Mock mode sends nothing externally.

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
      → configured narrative provider returns validated proposal
      → SimulationService + deterministic engine validate/apply
      → repositories flush events/snapshots/artifacts/messages
  → transaction commit
  → explicit Pydantic response
```

Universe generation validates the complete branch set before creating the
universes and their initial snapshots in one transaction. Annual advancement
persists a pending significant event without a snapshot when user input is
required. Choice resolution reconstructs the validated event and choices from
that persisted proposal, applies the selected effects once, schedules delayed
effects, creates the summary and artifact, and appends the final snapshot in a
single transaction. A provider or persistence exception rolls back all of it.

The scenario UI records optional branch directions in its bounded description
payload. Universe generation extracts that structured line and forwards the
directions to either narrative provider. A compatibility guard recognizes only
the old three demo directions on a completely pristine non-demo scenario; it
may rebuild that initial set transactionally. Any event, additional snapshot,
artifact, or future-self conversation makes the scenario ineligible, so repair
cannot erase played history.

Custom mock paths use separate education, career, and creator event catalogues
rather than the seeded AI/robotics/startup catalogue. A second compatibility
guard may replace an unselected pending mock event whose key came from the old
catalogue. It never touches a resolved event or snapshot, and the replacement
is created inside the same transaction.

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

The OpenAI adapter is optional and `mock` remains the complete offline default.
Historical universe forking remains deferred because
the Phase 5 backend does not expose a fork route; the detail screen labels that
control as unavailable instead of simulating a fork in browser state.

SQLite is the MVP store. Alembic will be the only schema-management path. The
local web boundary remains compatible with a future Tauri shell without adding
desktop concerns to the MVP.
