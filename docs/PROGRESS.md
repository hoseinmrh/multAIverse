# Progress

## Current phase

Phase 9 — Quality pass: **in progress** (repository-readiness pass completed
2026-08-27). The core application and Phase 8 OpenAI provider are implemented;
the mock provider remains the offline default, and automated checks make no real
OpenAI requests. Playwright coverage and a full interactive
accessibility/responsive walkthrough remain outstanding.

## Clean-clone setup follow-up

- Reworked the README around a clone-to-demo quick start, explicit network and
  platform expectations, seeded database behavior, project status, and honest
  Phase 9 limitations.
- Split backend-only root configuration from the browser-safe
  `frontend/.env.local` template, matching how Next.js actually loads
  environment files, and made both dev server hosts and ports configurable
  through Make parameters.
- Rechecked the public OpenAI model guidance against current official
  documentation and removed a brittle model-specific verbosity claim from the
  setup path; optional controls now default to unset and remain evaluation-led.
- Expanded generated-file ignores and removed the obsolete root `test.md`
  implementation-prompt scratchpad; its history remains recoverable through
  Git.

### Repository-readiness verification

- Isolated clean-copy `make setup` — installed all locked backend and frontend
  dependencies successfully.
- Isolated clean-copy `make seed` — upgraded from an empty SQLite database to
  Alembic head and seeded the three-universe demo.
- Isolated clean-copy `make dev` — backend and frontend started; `/api/v1/health`
  returned HTTP 200 and the landing page rendered successfully.
- `make test` — 69 backend tests and 24 frontend tests passed.
- `make lint` — Ruff and ESLint passed.
- `make format-check` — all backend and frontend files passed.
- `make typecheck` — strict MyPy checks passed across 63 source files and
  TypeScript reported no errors.
- `make build` — backend compilation and the Next.js production build passed.
- `uv run alembic current` / `uv run alembic check` — revision
  `8f4d3b2a1c0e (head)` and no schema drift.
- `make simulation-demo` — all three universes reached 2031 with six immutable
  snapshots each.
- Updated Markdown passed Prettier, and `git diff --check` passed.

## OpenAI runtime compatibility follow-up

- Confirmed with profile-free structured-output probes that the configured
  `gpt-5.6-luna` model and low reasoning work, while its Responses API currently
  rejects the optional verbosity parameter with HTTP 400
  `unsupported_parameter`.
- Disabled verbosity in the active local configuration. The provider now
  recognizes that safe error code and spends at most one configured retry on a
  compatibility request with both optional controls omitted instead of falling
  directly back to deterministic mock output.
- Added safe HTTP status metadata to provider failure logs without exposing
  exception messages, response bodies, prompts, profiles, or credentials.
- Added regression coverage for the compatibility retry, control omission,
  non-retryable bad requests, retry bounds, and sanitized status logging.
- Added GPT-only narrative mode through `OPENAI_FALLBACK_TO_MOCK=false`. In this
  mode, provider failure returns a safe error and rolls back instead of
  committing deterministic mock prose.
- Tagged universe generation provenance in `visual_theme` metadata. Untouched
  mock-authored universe sets are transactionally regenerated through OpenAI
  when reopened in GPT-only mode; played history remains immutable.
- Routed legacy pending-event refresh through the configured provider. Strict
  OpenAI mode also replaces any unselected mock pending decision without
  altering an existing snapshot or resolved choice.
- Replaced the engine routine event's visible deterministic title/description
  with the validated provider yearly summary before commit. Routine effects,
  financial calculations, caps, and state application remain deterministic.
- Strengthened the significant-event prompt to demand person- and
  universe-specific dilemmas, causal continuity, concrete opportunity costs,
  uncertainty, and non-template choices.
- Updated Settings provider status to distinguish “GPT only” from “GPT with
  mock fallback.” Added transaction tests proving unplayed mock stories become
  provider-authored, yearly decisions are sourced from OpenAI, visible yearly
  events are provider prose, and replacement failure preserves the old story.
- Corrected OpenAI strict schemas for dynamic skill, stat, effect, and
  requirement maps by using bounded unique `{key,value}` entries on the model
  wire and converting them back into the existing validated engine maps. All
  six output contracts now avoid unsupported dynamic object properties.
- Regenerated the latest untouched Hanisa scenario through the live configured
  provider. All three persisted universes report OpenAI provenance; no event or
  simulation year was advanced during the regeneration.

## Saved-story navigation follow-up

- Fixed primary navigation always opening the seeded demo scenario after a new
  person's scenario had been created successfully.
- Added `/stories`, a local library that groups every persisted scenario under
  its person and links directly to the correct three-universe map.
- Added entry points for the library in the application header and landing
  page, plus actions for another scenario from an existing person or a new
  person.
- Added frontend regression coverage proving both old and new profiles remain
  visible and link to their own scenario IDs. Scenario creation now invalidates
  the story-list cache.
- Fixed the underlying non-demo content mismatch: application generation now
  forwards the scenario form's custom branch directions, and the mock provider
  derives generic study, career, creator, or independent states instead of
  reusing Hosein's AI/robotics/startup labels.
- Opening a saved story now runs the idempotent generation check before routing.
  Pristine legacy scenarios with the three incorrect demo branches are repaired
  transactionally; any played history prevents replacement, and failure rolls
  the attempted repair back to the original universes.
- Added distinct education, general-career, and content-creator mock event
  catalogues. The universe screen detects old demo-catalogue pending events for
  custom paths and refreshes them before displaying a choice; resolved choices
  and state snapshots are never rewritten.
- Verified 69 backend tests and all 10 frontend test files/24 tests, Ruff,
  ESLint, formatting, strict Python and TypeScript checks, and the production
  build including the new `/stories` route. A browser walkthrough remains
  unavailable because no browser session was exposed to the workspace.

## Phase 8 completed work

- Added `OpenAINarrativeProvider` using the asynchronous Responses API and
  Pydantic Structured Outputs for universe branches, significant events, yearly
  summaries, structured artifacts, future-self profiles, and future-self
  replies. All six SDK output schemas convert to strict OpenAI JSON schemas.
- Added separate prompt builders for every task. Prompts treat supplied text as
  untrusted data, keep requests below 20,000 characters, cap model output, send
  only bounded context, and retain only eight recent chat messages.
- Refined prompts for economical GPT-5.6 use: compact outcome-first instructions,
  task-specific context fields, omission of unused effect/choice data, optional
  reasoning and verbosity controls, and output ceilings from 800 to 3,000 tokens.
  The documented starting point is Luna with low reasoning and verbosity
  unset; Terra is the quality upgrade when evaluation shows the extra prose
  quality is useful.
- Added semantic output checks for branch count/uniqueness, event years and
  duplicate keys, summary years, artifact/event linkage, stable future-self
  identity fields, and future-self references to stored event keys.
- Added backend configuration for provider, key, model, timeout, retries, and
  fallback. Mock remains the default, OpenAI has no hardcoded model, and an
  incomplete OpenAI configuration safely reports/uses mock fallback when
  enabled.
- Disabled SDK retries and added application-owned bounded retry/backoff for
  timeouts, connections, rate limits, invalid structured output, and empty
  responses. Authentication failures are not retried. Failure logs contain
  only safe operation/category/status metadata; API keys are secret-wrapped and
  hidden from configuration representations.
- Added mock fallback per narrative operation and provider-status reporting for
  ready, configured, fallback, and unavailable states. Public config includes
  no credential field, and the frontend Settings screen displays the safe
  status and configured model when applicable.
- Changed important-choice resolution to reconstruct the exact validated event
  and effects persisted when the choice was shown. OpenAI output is never
  regenerated for replay; the deterministic engine remains the only state
  mutation authority.
- Added failure-injection coverage proving OpenAI timeouts create no events or
  snapshots and leave universe time unchanged. Existing transaction tests
  continue to prove summary/artifact failures roll back choice and state
  changes.
- Added mocked SDK coverage for successful structured output across all tasks,
  invalid schemas, oversized and empty output, timeout, authentication failure,
  rate limiting, retry bounds, fallback, grounded future-self references,
  secret-free logging, input limits, and bounded chat history.
- Updated `.env.example`, README privacy/setup guidance, architecture/API docs,
  and the frontend provider-status presentation. The README now enumerates the
  exact profile, state, history, and chat fields sent only when OpenAI mode is
  enabled.

### Phase 8 verification

- `make test` — 57 backend tests and 21 frontend tests passed. API fixtures
  force mock mode so a developer's local OpenAI configuration cannot trigger a
  real request during the normal suite.
- `make lint` — Ruff and ESLint passed.
- `make format-check` — 66 backend files and all frontend files passed.
- `make typecheck` — strict MyPy passed across 63 source files and strict
  TypeScript passed.
- `make build` with the required Turbopack process permission — backend bytecode
  compilation and the Next.js production build passed for all nine routes.
- OpenAI SDK strict-schema conversion — all six narrative output schemas
  validated locally without a network request.

## Phase 6 onboarding reliability follow-up

- Replaced comma-normalized profile list textareas with explicit Add controls
  for goals, interests, strengths, growth edges, and constraints. Multi-word
  phrases now keep their spaces, Enter is an optional shortcut, added items are
  visible as removable chips, and duplicate entries are ignored.
- Kept the final profile action clickable whenever it is not actively saving.
  Validation and API errors are now surfaced after an attempted submission
  instead of leaving the user with a silently disabled button.
- Added an interaction-level regression test that enters multi-word profile
  details, adds them with both the button and Enter, completes onboarding,
  verifies the create request payload, and verifies scenario navigation.
- Verified a real profile create request against the running FastAPI service;
  the response preserved all multi-word list items and returned `201 Created`.
  The temporary verification profile was deleted immediately afterward.

### Follow-up verification

- `pnpm --dir frontend format:check` — passed.
- `pnpm --dir frontend lint` — passed.
- `pnpm --dir frontend typecheck` — strict TypeScript passed.
- `pnpm --dir frontend test` — 8 files and 20 tests passed.
- `pnpm --dir frontend build` — Next.js production build passed with all nine
  application routes.

## Phase 6 scenario-generation reliability follow-up

- Fixed newly generated universes being persisted successfully but rejected by
  the frontend as an unexpected response. Zod 4's integer schema requires a
  JavaScript-safe integer, while deterministic universe seeds previously used
  the wider signed 64-bit database range.
- Made new universe seeds remain within JavaScript's exact integer range while
  retaining deterministic derivation and backend ownership of randomness.
- Kept existing universes compatible without rewriting or migrating their
  persisted seeds. The frontend treats legacy 64-bit seed values as opaque
  integer response data because it never performs simulation with them.
- Added regression coverage for parsing a real legacy-scale seed, rejecting
  fractional seeds, and ensuring every newly generated seed is browser-safe.

### Scenario-generation follow-up verification

- `cd backend && uv run pytest` — 42 tests passed.
- `cd backend && uv run ruff check app tests migrations ../scripts` — passed.
- `cd backend && uv run ruff format --check app tests migrations ../scripts` —
  63 files already formatted.
- `cd backend && uv run mypy app tests ../scripts` — strict type checking passed
  across 60 source files.
- `cd backend && uv run alembic check` — no schema drift or new upgrade
  operations detected.
- `cd backend && uv run python -m compileall -q app migrations ../scripts` —
  passed.

## Phase 6 completed work

- Replaced the foundation screen with a polished dark, deep-space landing page,
  immediate seeded-demo entry, fictional-simulation disclaimer, live mock-
  provider status, and a seven-step profile onboarding flow.
- Added strict Zod validation for frontend inputs and every consumed backend
  response. Added one typed API client for all `/api/v1` calls; no feature
  component contains a raw fetch.
- Added scenario creation with fixed three-branch generation, all five
  simulation modes, context, time horizon, optional branch direction notes, and
  real profile/scenario/generation mutations.
- Added the React Flow multiverse map with a central reality, three themed
  universe nodes, readable vertical event chains, pending-choice indicators,
  fit/zoom/pan controls, minimap, and keyboard-reachable universe navigation.
- Added complete universe detail with current year/age/location/career, eight
  semantic statistic cards, finance summary, immutable timeline, achievements,
  active flags, artifacts, yearly advancement, blocking decision dialog,
  idempotent choice selection, per-universe reset, and future-self entry.
- Added type-specific artifact layouts for news, academic abstracts, company
  announcements, diary entries, email, and social posts plus a focused artifact
  viewer.
- Added comparison with radar and timeline charts for current stats, happiness,
  stress, and net worth; accessible hidden tables; career/financial summaries;
  key decisions, achievements, regrets; and a non-ranking written comparison.
- Added mock future-self conversation creation, grounded identity card,
  suggested questions, keyboard-friendly composer, atomic message updates, and
  loading/error states.
- Added settings for provider/version status, local simulation defaults, stored
  reduced-motion preference, disclaimer, and a real backend reset across all
  three seeded demo universes. No credential field exists.
- Added coordinated TanStack Query invalidation after universe generation,
  yearly advancement, choice selection, reset, and future-self messages.
- Added responsive 1440×900, 1280×800, tablet, and basic mobile layouts;
  `prefers-reduced-motion`; explicit motion override; skip links; visible focus;
  semantic meters; dialog focus trapping; and accessible chart data.
- Added a generated, product-specific social preview asset at
  `frontend/public/og.png` and host-derived Open Graph/X metadata.
- Added 18 frontend tests covering profile/scenario validation, universe nodes,
  statistic cards, decisions, timeline rendering, all artifact layouts,
  comparison data, future-self chat, provider status, and loading/failure states.

## Phase 6 verification

- `pnpm --dir frontend format:check` — passed.
- `pnpm --dir frontend lint` — passed.
- `pnpm --dir frontend typecheck` — strict TypeScript passed.
- `pnpm --dir frontend test` — 7 files and 18 tests passed.
- `pnpm --dir frontend build` — Next.js 16 production build passed with all nine
  application routes.
- Live local HTTP smoke verification — landing and seeded-map routes returned
  successfully; the Applied AI universe advanced from 2026 to a real pending
  2027 decision; selecting the measured option created the 2027 snapshot and a
  news artifact; comparison reflected the update; and a future-self conversation
  persisted a user/reply pair. The temporary verification history was reset, so
  the handed-off demo remains at the clean 2026 seed.
- In-app browser initialization and troubleshooting were attempted, but the
  runtime returned an empty browser list. A visual click-through was therefore
  not claimed.

## Phase 5 completed work

## Phase 5 completed work

- Added the full explicit-schema FastAPI surface under `/api/v1`: public
  configuration, profile CRUD, scenario create/list/detail, idempotent universe
  generation, universe/state/timeline reads, advancement, reset, event/choice
  reads and resolution, comparison, artifacts, and future-self conversations.
- Added `CoreApplicationService` as the transaction-owning composition layer.
  Routes contain only transport concerns; repositories still flush without
  committing, providers remain persistence-free, and the deterministic engine
  remains the only state-transition authority.
- Integrated mock narrative branches and significant events into persisted API
  flows. Provider effects reuse strict engine schemas and are capped during
  deterministic annual finalization.
- Made unresolved narrative choices block further advancement. Choice replay
  checks the persisted narrative key, validates requirements, applies effects
  exactly once, schedules delayed consequences, appends one immutable snapshot,
  and unblocks the universe.
- Made repeated selection of the same choice return the existing snapshot with
  `idempotent: true`; conflicting selections return a consistent 409 error and
  never apply effects.
- Made universe generation, choice finalization plus artifact generation,
  reset, conversation creation, and future-self user/reply insertion atomic.
  Failure-injection integration tests prove provider failures roll back universe
  and yearly state changes.
- Added deterministic structured artifact persistence, artifact detail/list
  routes, and comparison responses with current state, finances, achievements,
  regrets, decisions, histories, and named score components without a single
  best-universe score.
- Added stable persisted future-self personality summaries, grounded identity
  cards, conversation retrieval, and atomic mock messaging.
- Added offset/limit/total/has-more pagination to every growing collection and
  one safe error envelope for validation, domain conflicts, persistence errors,
  provider failures, missing routes, and unexpected failures.
- Added Alembic revision `8f4d3b2a1c0e` for event narrative keys and stable
  future-self personality summaries.
- Added complete API happy-path coverage: load demo profile/scenario, obtain all
  three universes, advance, verify blocking, resolve and repeat a choice,
  retrieve timeline/artifacts, compare branches, chat with a future self, and
  reset. Separate tests cover new-scenario generation, CRUD, pagination,
  secret-free configuration, error shapes, and transaction rollback.

## Phase 4 completed work

- Added a runtime-checkable asynchronous `NarrativeProvider` protocol covering
  universe branches, significant events, yearly summaries, structured
  artifacts, future-self profiles, and future-self responses.
- Added immutable, extra-forbidding Pydantic contracts for all generated
  content. Event choices reuse Phase 3's validated effects, delayed effects,
  requirements, and risk levels; unknown effect statistics remain rejected.
- Added a concise narrative context builder with bounded profile detail,
  universe premise, current state, important flags, three recent major events,
  duplicate-prevention keys, unresolved decisions, long-term summary, mode,
  year, and the explicit effect allowlist.
- Implemented the offline `MockNarrativeProvider` with deterministic seeded
  variation. It has no database session, repository, API key, internet client,
  global randomness, or state-mutation function.
- Added generation for Applied AI Leader, Robotics Researcher, and Startup
  Founder with distinct premises, visual themes, roles, skills, finances, and
  flags.
- Added path-specific and shared significant events across career, research,
  startup, finance, health, relationships, opportunities, crises, and
  mode-specific random events. Acute state constrains selection and used event
  keys are excluded.
- Added distinct Realistic, Cinematic, Utopian, Dark, and Chaos selection/tone
  behavior without letting narrative mode bypass deterministic processing.
- Added yearly summaries and six structured artifact families: news article,
  academic abstract, company announcement, diary entry, email, and
  social/professional post. Artifacts identify themselves as fictional.
- Added stable future-self profiles and replies grounded in supplied state and
  recorded event keys; replies cannot cite an unrecorded major event.
- Added `make mock-narrative-demo`. It migrates and seeds an ephemeral database,
  then composes the pure engine with only the mock provider for five years in
  all three universes, including summaries, artifacts, and future-self replies.
- Added unit and integration coverage for schema closure, effect validation,
  protocol compliance, branch/event replay, duplicate prevention, state/mode
  selection, required categories and artifact shapes, context bounds, provider
  isolation, future-self grounding, and three-universe five-year replay.

No persisted schema changed in Phase 4, so Alembic revision `5bd72efdd0ea`
remains current.

## Phase 3 completed work

- Added a pure deterministic engine isolated from FastAPI, SQLAlchemy, and all
  narrative-provider code.
- Added namespaced SHA-256 seed derivation and local seeded PRNG streams for
  event selection, market timing, path outcomes, and probabilistic delayed
  consequences. The engine never uses global randomness.
- Added a deeply immutable in-memory simulation state and append-only persisted
  yearly snapshots.
- Added strict effect, finance, delayed-effect, and choice-requirement schemas;
  unknown statistics, extra fields, malformed values, and invalid probabilities
  are rejected.
- Added immediate effects, delayed scheduling and application, seeded
  probability resolution, flags, skills, per-effect caps, diminishing returns,
  stronger high-stress penalties, aggregate annual caps, and 0–100 clamping.
- Added yearly baseline recovery, prolonged extreme-stress health damage,
  nonlinear happiness, burnout risk, career/research/startup momentum, and
  mode-adjusted success/setback selection with nonzero outcome tails.
- Added annual income growth, bounded saving behavior, startup runway pressure,
  positive asset returns, debt interest, and net-worth updates without treating
  money as a proxy for happiness.
- Added deterministic routine/significant system events and choices. These are
  static engine configuration; no narrative provider or LLM is present.
- Added a transaction-owning simulation service that blocks unresolved choices,
  validates requirements, applies selections atomically, schedules delayed
  effects, advances universe cursors, and appends one final snapshot per year.
- Made choice resolution idempotent: selecting the same choice again returns the
  existing state without applying any effect twice, while conflicting choices
  are rejected.
- Added `make simulation-demo`, which migrates an ephemeral database, seeds the
  three required universes, auto-selects deterministic choices, advances each
  five years from 2026 to 2031, prints final results, and uses no LLM.
- Added unit/integration coverage for seeded replay, immutability, effect
  validation/application, delayed and probabilistic effects, clamping, stress,
  happiness, burnout, finances, all momentum families, unresolved blocking,
  idempotency, and full three-universe five-year reproducibility.
- Updated the root/backend guides, implementation plan, game design, and
  architecture documentation for Phase 3.

## Prior completed work

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

## Phase 5 verification

- `cd backend && uv run pytest` — 42 backend tests passed.
- `cd backend && uv run ruff check app tests migrations ../scripts` — passed.
- `cd backend && uv run ruff format --check app tests migrations ../scripts` —
  63 files already formatted.
- `cd backend && uv run mypy app tests ../scripts` — strict type checking
  passed across 60 source files.
- `cd backend && uv run alembic upgrade head` — upgraded the local database from
  `5bd72efdd0ea` to `8f4d3b2a1c0e`.
- `cd backend && uv run alembic current` — `8f4d3b2a1c0e (head)`.
- `cd backend && uv run alembic check` — no schema drift or new upgrade
  operations detected.
- `cd backend && uv run python -m compileall -q app migrations ../scripts` —
  passed.
- FastAPI OpenAPI generation — passed with 21 documented `/api/v1` paths.
- `git diff --check` — passed.

## Phase 4 verification

All final checks passed:

- `cd backend && uv run pytest` — 36 backend tests passed.
- `cd backend && uv run ruff check app tests migrations ../scripts` — passed.
- `cd backend && uv run ruff format --check app tests migrations ../scripts` —
  51 files already formatted.
- `cd backend && uv run mypy app tests ../scripts` — strict type checking
  passed across 49 source files.
- `cd backend && uv run alembic check` — no schema drift or new upgrade
  operations detected.
- `cd backend && uv run python -m compileall -q app migrations ../scripts` —
  passed.
- `make mock-narrative-demo` — Applied AI Leader, Robotics Researcher, and
  Startup Founder each reached 2031 with five unique narrative events, five
  summaries, five structured artifacts, and a future-self reply. No API key or
  network access was used.
- `git diff --check` — passed.

Phase 2 migration, seed, complete repository, and immutability verification
remain covered by the same backend suite. No schema change was needed in Phase
3, so migration revision `5bd72efdd0ea` remains current.

## Known limitations

- OpenAI availability and model compatibility are configuration-dependent and
  were not tested against the live service; the normal suite intentionally uses
  mocked SDK responses only.
- Historical universe forking remains unavailable because there is no Phase 5
  fork API. The frontend leaves the control disabled rather than inventing
  client-only history.
- Visual browser walkthrough remains pending an available in-app browser
  session. Automated frontend checks, the production build, server-rendered
  route smoke checks, and the full live API flow passed.
- `make reset-db` intentionally destroys existing local simulation data before
  restoring the demo seed.
- pnpm continues to report that it blocks the optional `unrs-resolver`
  lifecycle script; current tests and builds do not require it.

## Next task

Phase 9 — Quality pass: accessibility, responsive-layout review, an available
interactive browser walkthrough, end-to-end coverage, and final documentation
review.
