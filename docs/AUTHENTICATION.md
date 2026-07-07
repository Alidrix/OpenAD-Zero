# Local API Authentication

OpenAD-Zero supports a minimal local API-token mode for protecting sensitive REST endpoints and WebSocket handshakes before operator approval workflows are added.

## Default development mode

Authentication is disabled by default so existing local development and Docker healthchecks continue to work:

```env
OPENADZERO_AUTH_ENABLED=false
OPENADZERO_API_TOKEN=
OPENADZERO_ALLOW_UNAUTHENTICATED_LOCALHOST=true
OPENADZERO_AUTH_PROTECT_DOCS=false
```

`/api/health` stays public for Compose and container healthchecks.

## Enabling authentication

Set a long, random local token in `.env` and do not commit that file:

```env
OPENADZERO_AUTH_ENABLED=true
OPENADZERO_API_TOKEN=change-this-local-token
OPENADZERO_ALLOW_UNAUTHENTICATED_LOCALHOST=true
OPENADZERO_AUTH_PROTECT_DOCS=false
```

Use a generated high-entropy value for real local operations. The backend never returns the configured token through `/api/auth/status` and must not log it.

Clients authenticate HTTP requests with:

```http
Authorization: Bearer <token>
```

Do not put secrets in frontend build-time variables such as `VITE_*`. The frontend settings page stores the operator-provided token in browser storage and attaches it at request time.

## Localhost bypass

When `OPENADZERO_ALLOW_UNAUTHENTICATED_LOCALHOST=true`, only direct peer addresses that are actually local (`127.0.0.0/8`, `::1`, or `localhost`) bypass the token. OpenAD-Zero does not trust `X-Forwarded-For` by default because direct clients can spoof it unless a trusted proxy sanitizes headers.

## WebSockets

Protected WebSockets accept the token during the handshake by query parameter (`?token=...`) or an `Authorization: Bearer ...` header when the client can send one. The token is never accepted from WebSocket messages or command payloads.

## Public endpoints

These endpoints remain public:

- `GET /api/health`
- `GET /api/version`
- `GET /api/auth/status` (returns booleans only, never the token)

## Protected endpoints

When auth is enabled, sensitive mission, evidence, report, operations, capabilities, jobs/events, tool automation, V2 scans, V2 parsing, V2 recommendations, V2 dashboard, V2 pentest orchestrator, and detailed health endpoints require a valid bearer token. Detailed health endpoints include `/api/health/db`, `/api/health/redis`, `/api/health/tools`, and `/api/health/worker`.


## Prod-like guardrails

Set `OPENADZERO_ENV=prod-like` and `OPENADZERO_AUTH_ENABLED=true`. Provide `OPENADZERO_API_TOKEN` or preferably `OPENADZERO_API_TOKEN_FILE=/run/secrets/openadzero_api_token`. The backend refuses empty tokens and weak placeholders in prod-like mode. `/api/auth/status` reports only booleans and never returns the token value.
