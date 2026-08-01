# API

All application routes are versioned under `/api/v1`. FastAPI publishes the
generated OpenAPI document at `/openapi.json` and interactive documentation at
`/docs`.

## Health

`GET /api/v1/health`

Response:

```json
{
  "status": "ok",
  "service": "Multiverse API",
  "version": "0.1.0"
}
```

The endpoint has no persistence or external-service dependency. The frontend
uses it to show local backend connectivity.

Profile, scenario, universe, event, artifact, comparison, and future-self
routes are intentionally deferred to their specification phases.
