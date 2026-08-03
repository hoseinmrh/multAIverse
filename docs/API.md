# API

All application routes are versioned under `/api/v1`. FastAPI publishes the
generated OpenAPI document at `/openapi.json` and interactive documentation at
`/docs`. Request and response bodies use explicit Pydantic schemas.

## Conventions

Growing collections accept `offset` (default `0`) and `limit` (default `20`,
maximum `100`) and return:

```json
{
  "items": [],
  "pagination": {
    "offset": 0,
    "limit": 20,
    "total": 0,
    "has_more": false
  }
}
```

Errors use one envelope for validation, domain, persistence, and unexpected
failures. Validation details never echo the submitted value.

```json
{
  "error": {
    "code": "not_found",
    "message": "Universe was not found",
    "details": {"id": "30000000-0000-4000-8000-000000000001"}
  }
}
```

Important codes are `validation_error` (422), `not_found` (404), `conflict`
(409), `invalid_operation` (400), `narrative_unavailable` (503), and
`internal_error` (500).

## System

- `GET /health` checks backend availability without touching persistence.
- `GET /config/public` returns the application name/version, active provider,
  supported modes, branch limit, and fictional-simulation disclaimer. It never
  returns credentials or backend-only configuration.

Health response:

```json
{
  "status": "ok",
  "service": "Multiverse API",
  "version": "0.1.0"
}
```

## Profiles

- `POST /profiles`
- `GET /profiles?offset=0&limit=20`
- `GET /profiles/{profile_id}`
- `PATCH /profiles/{profile_id}`
- `DELETE /profiles/{profile_id}`

Create example:

```json
{
  "name": "Ada",
  "birth_year": 1996,
  "starting_year": 2026,
  "starting_age": 30,
  "location": "Turin",
  "occupation": "Engineer",
  "education": "MSc",
  "strengths": ["Systems thinking"],
  "interests": ["Robotics"],
  "starting_stats": {"health": 75, "happiness": 68}
}
```

Deleting a profile cascades to its scenarios and their universe histories.

## Scenarios and universe generation

- `POST /scenarios`
- `GET /scenarios?profile_id={profile_id}&offset=0&limit=20`
- `GET /scenarios/{scenario_id}` returns the scenario and current universes.
- `POST /scenarios/{scenario_id}/generate-universes`
- `GET /scenarios/{scenario_id}/comparison`

Scenario create example:

```json
{
  "profile_id": "10000000-0000-4000-8000-000000000001",
  "title": "After Graduation",
  "decision_question": "What should I prioritize after graduation?",
  "description": "Explore three fictional alternatives.",
  "number_of_universes": 3,
  "simulation_mode": "realistic",
  "seed": 202600
}
```

Generation calls the configured narrative provider, validates all three branch
schemas, derives stable universe seeds, and persists each universe plus its
initial immutable snapshot in one transaction. Repeating the call returns the
complete existing set with `generated: false`; a partial existing set is a 409
conflict rather than being silently repaired.

Comparison returns each universe's current normalized statistics, finances,
location, career summary, achievements, regrets, decisions, happiness/stress/
net-worth history, and several named score components. It intentionally does
not declare a single best universe or return one aggregate score.

## Universes and timelines

- `GET /universes/{universe_id}`
- `GET /universes/{universe_id}/state`
- `GET /universes/{universe_id}/timeline?offset=0&limit=20`
- `POST /universes/{universe_id}/advance`
- `POST /universes/{universe_id}/reset`
- `GET /universes/{universe_id}/events?offset=0&limit=20`
- `GET /universes/{universe_id}/artifacts?offset=0&limit=20`

Advancement asks the mock provider for a schema-validated significant event,
then passes every proposed effect through the deterministic engine. A required
choice produces `blocked: true`, persists the event and choices, and does not
append the target year's snapshot. Further advancement returns 409 until that
choice is resolved.

Reset atomically removes events, choices, delayed effects, generated artifacts,
conversations, messages, and all snapshots after the initial state. It preserves
the immutable initial snapshot and restores the universe cursor to it.

## Events and choices

- `GET /events/{event_id}` returns an event with all choices.
- `POST /events/{event_id}/choices/{choice_id}/select`

Selection validates ownership and requirements, deterministically replays the
pending year, applies immediate effects through the engine, schedules delayed
effects, generates a summary and one structured artifact, appends the immutable
snapshot, and unblocks the universe in one transaction.

Selecting the same choice again is idempotent: the response has
`idempotent: true` and returns the existing snapshot without reapplying effects
or creating another artifact. Selecting a different choice after resolution is
a 409 conflict.

## Artifacts

- `GET /universes/{universe_id}/artifacts?offset=0&limit=20`
- `GET /artifacts/{artifact_id}`

Artifact content is type-specific structured JSON. Mock artifacts include
`metadata.is_fictional: true` and use fictional supporting organizations and
characters.

## Future self

- `POST /universes/{universe_id}/future-self/conversations`
- `GET /future-self/conversations/{conversation_id}?offset=0&limit=50`
- `POST /future-self/conversations/{conversation_id}/messages?offset=0&limit=50`

Conversation create body (an empty object uses the generated title):

```json
{"title": "Questions for my future self"}
```

Message body:

```json
{"content": "What decision changed your life most?"}
```

Conversation responses contain a fictional-character identity card, the
persisted stable personality summary, a page of messages, and pagination
metadata. User and future-self messages are inserted together only after a
reply is successfully generated, so provider failure cannot leave a one-sided
exchange.

## Transaction behavior

Repositories only flush. Application services own commits and group each state
change into one transaction. Provider, validation, effect, artifact, or
persistence failures roll the transaction back. Narrative providers receive
bounded values and never receive a database session or mutate state directly.
