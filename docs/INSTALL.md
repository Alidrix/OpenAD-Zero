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
