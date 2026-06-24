# Installation

## Prerequisites

- Docker and Docker Compose v2
- Make

## Configure

```bash
cp .env.example .env
```

Keep `OPENADZERO_AUTO_CREATE_TABLES=false` and run migrations explicitly. Change BloodHound `change-me-*` values before any non-local use.

## Start

```bash
make up-build
make migrate
```

Open the UI at http://localhost:5173 and the API at http://localhost:8000.

## Troubleshooting

Use `make ps`, `make logs-api`, `make logs-worker`, and `make health`. Health endpoints are under `/api/health`, `/api/health/db`, `/api/health/redis`, `/api/health/tools`, and `/api/health/worker`.
