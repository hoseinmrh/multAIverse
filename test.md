## Phase 4 — Mock Narrative Provider

Implement Phase 4 from `@docs/PRODUCT_SPEC.md`: the mock narrative provider.

The application must remain fully functional without an API key or internet access.

Implement and test:

* narrative provider protocol or interface
* strict Pydantic schemas for generated content
* mock universe branch generation
* mock significant-event generation
* state-aware event selection
* yearly narrative summaries
* structured artifact generation
* future-self profile generation
* future-self replies
* seeded and reproducible narrative variation
* duplicate-event prevention
* simulation-mode-specific content
* narrative context builder

Keep the narrative provider separate from the deterministic simulation engine.

Narrative providers must not:

* write directly to the database
* mutate simulation state
* apply effects directly
* bypass effect validation

Support at least:

* Applied AI Leader
* Robotics Researcher
* Startup Founder

Support event categories including career, research, startup, finance, health, relationships, opportunities, and crises.

Create a demonstration that simulates all three seeded universes for five years using only the mock provider.

Run the complete backend test suite, linting, formatting, and type checks.

Update:

* `@docs/PROGRESS.md`
* `@docs/ARCHITECTURE.md`
* `@docs/GAME_DESIGN.md`
* `.env.example`

Do not implement the OpenAI provider or frontend screens yet.

---

## Phase 5 — Backend APIs

Implement Phase 5 from `@docs/PRODUCT_SPEC.md`: the FastAPI backend APIs.

Use versioned routes under:

```text
/api/v1
```

Expose the existing persistence layer, simulation engine, and mock narrative provider through thin API routes and application services.

Implement and test:

* health and public configuration routes
* profile CRUD
* scenario creation and retrieval
* universe generation
* universe state and timeline retrieval
* yearly advancement
* event and choice retrieval
* idempotent choice selection
* universe reset
* universe comparison
* artifact retrieval
* future-self conversation creation
* future-self messaging
* pagination for growing collections
* consistent API error responses
* transaction-safe state changes
* rollback on failures

Ensure:

* route handlers contain minimal business logic
* unresolved choices block advancement
* repeated choice requests do not apply effects twice
* universe generation is transaction-safe
* API responses never expose secrets
* all responses use explicit Pydantic schemas

Add integration tests covering the complete backend happy path:

1. Load the demo profile
2. Create or retrieve the demo scenario
3. Generate three universes
4. Advance one universe
5. Resolve a choice
6. Retrieve artifacts
7. Compare universes
8. Start a future-self conversation

Run the full backend test suite, migrations, linting, formatting, and type checks.

Update:

* `@docs/API.md`
* `@docs/ARCHITECTURE.md`
* `@docs/PROGRESS.md`
* `README.md`

Do not implement the main frontend screens yet.

---

## Phase 6 — Frontend Application

Implement Phase 6 from `@docs/PRODUCT_SPEC.md`: the complete frontend MVP.

Use the existing backend APIs and mock narrative provider.

Implement:

* landing page
* demo entry flow
* profile onboarding
* scenario creation
* multiverse map using React Flow
* universe detail screen
* statistics display
* timeline
* yearly advancement flow
* event decision modal
* artifact viewer
* universe comparison screen
* future-self chat
* settings and provider-status screen
* loading, empty, and error states
* responsive laptop layout
* reduced-motion support
* accessible keyboard navigation

Use:

* Next.js
* TypeScript strict mode
* Tailwind CSS
* TanStack Query
* Zod
* React Flow
* Framer Motion
* the configured chart library

Create a typed API client instead of scattering raw fetch calls across components.

Ensure frontend state refreshes correctly after:

* universe generation
* yearly advancement
* choice selection
* reset
* future-self messages

Do not use frontend-only fake simulation data. All major actions must use the actual backend APIs.

Add frontend tests for:

* profile and scenario validation
* universe nodes
* statistic cards
* event choices
* timeline rendering
* artifact layouts
* comparison data
* future-self chat
* loading and failure states

Run frontend linting, formatting, type checking, tests, and the production build.

Manually verify the seeded demo flow from landing page through comparison and future-self chat.

Update:

* `@docs/PROGRESS.md`
* `@docs/ARCHITECTURE.md`
* `README.md`

Do not implement the OpenAI provider yet.

---

## Phase 7 — OpenAI Narrative Provider

Implement Phase 7 from `@docs/PRODUCT_SPEC.md`: the optional OpenAI narrative provider.

The mock provider must remain the default and must continue working without an API key.

Implement and test:

* `OpenAINarrativeProvider`
* provider factory and configuration
* OpenAI Responses API integration
* structured outputs using existing Pydantic schemas
* separate prompt builders for each narrative task
* universe branch generation
* significant-event generation
* yearly summaries
* artifact generation
* future-self profiles
* future-self replies
* bounded retries and timeouts
* sanitized logging
* mock-provider fallback
* provider-status reporting
* input and output size limits

Support configuration through:

```env
NARRATIVE_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_MODEL=
OPENAI_TIMEOUT_SECONDS=30
OPENAI_MAX_RETRIES=2
OPENAI_FALLBACK_TO_MOCK=true
```

Ensure:

* API keys remain backend-only
* API keys never appear in logs or API responses
* generated effects pass through the deterministic engine
* provider failures do not modify simulation state
* invalid structured output is rejected
* history sent to the model is concise and bounded
* future-self replies remain grounded in the stored timeline

Do not call the real OpenAI API in the normal automated test suite.

Mock SDK responses to test:

* successful structured output
* invalid schema
* timeout
* authentication failure
* rate limiting
* empty response
* bounded retries
* fallback to mock
* state preservation after failure

Update the frontend provider-status screen.

Run all backend and affected frontend tests, linting, formatting, type checks, and builds.

Update:

* `.env.example`
* `README.md`
* `@docs/ARCHITECTURE.md`
* `@docs/PROGRESS.md`

Document what profile information is sent to OpenAI when this provider is enabled.

---

## Phase 8 — Testing and Final Review

Implement Phase 8 from `@docs/PRODUCT_SPEC.md`: testing, hardening, and final review.

Do not add major new features during this phase.

Audit and test:

* MVP acceptance criteria
* deterministic reproducibility
* statistic invariants
* delayed effects
* choice idempotency
* unresolved-choice blocking
* five-year and ten-year simulation stability
* clean database migration
* seed idempotency
* transaction rollback
* API validation and error responses
* frontend query invalidation
* duplicate submission prevention
* loading and error states
* accessibility
* secret handling
* generated-content safety
* mock mode without an API key
* graceful OpenAI failure and fallback

Create or complete a Playwright end-to-end test that:

1. Starts from a clean test database
2. Opens the demo
3. Displays three universes
4. Opens a universe
5. Advances one year
6. Resolves a choice
7. Confirms state changes
8. Opens an artifact
9. Opens the comparison screen
10. Starts a future-self conversation
11. Sends a message

Create:

* `docs/ACCEPTANCE_CHECKLIST.md`
* `docs/FINAL_REVIEW.md`

Update all documentation so it matches the actual implementation.

Remove confirmed:

* dead code
* unused dependencies
* debug logs
* temporary files
* committed databases
* stale documentation
* commented-out experiments

Run:

* database reset and migration
* seed scripts
* complete backend tests
* complete frontend tests
* linting
* formatting checks
* backend type checks
* frontend type checks
* frontend production build
* Playwright end-to-end tests

Fix all confirmed issues caused by the repository.

Update `@docs/PROGRESS.md` with:

* completed phases
* exact verification results
* passed and failed acceptance criteria
* known limitations
* deferred features
* recommended next steps
