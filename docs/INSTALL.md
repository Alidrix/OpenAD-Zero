# Installation

## Prerequisites

- Docker and Docker Compose v2.
- Make.

## Configure

```bash
cp .env.example .env
```

Keep `OPENADZERO_AUTO_CREATE_TABLES=false` and run migrations explicitly. Change all `change-me-*` BloodHound values before any non-local use.

## Start

```bash
make up-build
make migrate
make smoke
```

Open the UI at http://localhost:5173 and the API at http://localhost:8000.

## Version

The release candidate version is stored in `VERSION` and exposed through `GET /api/version`. Docker backend images may use the built-in fallback `0.1.0-rc1` if the root version file is not present in the backend build context.

## Troubleshooting

Use `make ps`, `make logs-api`, `make logs-worker`, and `make health`. Health endpoints are under `/api/health`, `/api/health/db`, `/api/health/redis`, `/api/health/tools`, and `/api/health/worker`.

## Docker volumes and runtime permissions

The default Compose stack uses named volumes for `/app/evidence` and `/app/runtime`. The backend entrypoint starts as root only long enough to create and repair those mounted directories, then executes the API or worker as `APP_UID:APP_GID` (`10001:10001` by default). This preserves automatic volume permission repair while keeping the application runtime non-root.

`scripts/smoke.sh` verifies both the API and worker are running as UID/GID `10001:10001` and that `/app/evidence` plus `/app/runtime` are writable. If you replace the named volumes with bind mounts, ensure the mounted paths can be chowned by the container entrypoint or pre-create them with compatible ownership.


## Prompt 15 dev quick start

Copy `.env.example` to `.env`, generate a local token (`python -c "import secrets; print(secrets.token_urlsafe(32))"`), set `OPENADZERO_API_TOKEN`, then run `docker compose up -d`. Apply migrations with `make migrate`, verify with `cd backend && alembic heads`, and run `make smoke`. Optional services use profiles: default/dev for API/worker/UI/Postgres/Redis, `bloodhound` for BloodHound/Neo4j, and `prod-like` documented in `docs/DEPLOYMENT_PROD_LIKE.md`.
