# V2 Final QA Runbook

This runbook validates the OpenAD-Zero V2 local/prod-like workflow without bypassing auth, approvals, scope validation, or high-risk guardrails.

## Local prerequisites

- Docker and Docker Compose v2.
- `make`.
- Node.js/npm for local frontend builds.
- Python environment with backend test dependencies for local backend checks.
- A private/lab target scope only; never point QA scripts or UI flows at public IP ranges.

## Local startup

```bash
cp .env.example .env
docker compose up -d --build
make migrate
make smoke
```

Do not commit `.env`. Keep `ALLOW_PUBLIC_SCANS=false` for QA.

## Auth

Auth can be enabled with:

```bash
OPENADZERO_AUTH_ENABLED=true
OPENADZERO_API_TOKEN=<local-random-token>
```

Prefer setting those values in `.env` or exporting `OPENADZERO_API_TOKEN` in your shell. Test auth status with:

```bash
curl -fsS -H "Authorization: Bearer $OPENADZERO_API_TOKEN" http://localhost:8000/api/auth/status
```

`/api/auth/status` reports auth configuration status only and must not reveal the token.

## API QA

```bash
./scripts/v2-api-smoke.sh
```

When auth is enabled, export `OPENADZERO_AUTH_ENABLED=true` and `OPENADZERO_API_TOKEN` first. The script sends the bearer token but never prints it.

## Complete local QA

```bash
./scripts/local-e2e-qa.sh
```

The script checks Docker/Compose, creates `.env` from `.env.example` if missing, generates a local token only when auth is enabled and the token is blank, rebuilds the stack, waits for `/api/health`, runs migrations, checks schema health, checks the frontend if reachable, and runs the V2 API smoke script.

## Manual UI workflow

1. Open the frontend at `http://localhost:5173`.
2. Go to `Settings/Auth`.
3. Configure the local token if auth is enabled.
4. Open `Attack Control Center`.
5. Select a scan scoped to private lab ranges only.
6. Click `Start initial discovery` only for authorized private scope.
7. Verify parsed assets/services/signals and proposed actions.
8. Click `Review` on a supported safe action.
9. Click `Prepare approval`.
10. Review the masked server-side preview and scope snapshot.
11. Click `Approve`.
12. Use `Approve & Run` only for safe supported templates.
13. Verify events, artifacts, post-run normalization, recompute, and final action/job state.

## Manual Docker QA required when CI/Codex skips Docker

If Docker is unavailable or intentionally skipped with `OPENADZERO_RELEASE_CHECK_SKIP_DOCKER=1`, run locally:

```bash
docker compose config
docker compose down -v
docker compose up -d --build
docker compose ps
make migrate
make smoke
./scripts/v2-api-smoke.sh
./scripts/local-e2e-qa.sh
```

Confirm `openadzero-api` is healthy, `openadzero-worker` is running, Postgres and Redis are running, the frontend is accessible, `/api/health` is OK, `/api/health/schema` is OK, and `/api/auth/status` reveals no secret.

## Known limitations

- Not a multi-user SaaS deployment.
- Prod-like local workflow only; production hardening remains operator-owned.
- High-risk actions remain manual-only, preview-only, or blocked.
- Metasploit execution remains locked.
- Docker is required for complete smoke and worker QA.
- The QA scripts do not launch Metasploit, DonPAPI, Coercer, Responder, secretsdump, Mimikatz, public scans, or high-risk templates.
