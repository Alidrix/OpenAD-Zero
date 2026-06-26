# Development

## Structure

- `backend/`: FastAPI, SQLAlchemy models, RQ worker, Alembic migrations, integrations, evidence and reporting services.
- `frontend/`: React, TypeScript, Vite, Tailwind cockpit.
- `scripts/`: migration, reset, seed, smoke, security and release helpers.
- `VERSION`: centralized release candidate version.

## Backend

```bash
make backend-install
make backend-lint
make backend-format-check
make backend-test
```

## Frontend

```bash
make frontend-install
make frontend-build
```

## Worker

The worker runs `python -m app.worker` and has a Docker healthcheck using `python -m app.healthcheck_worker`.

## Seed data

Seed data is explicit only:

```bash
make seed-dev
```

## Evidence directory

OpenAD Zero stores generated evidence under `EVIDENCE_DIR`.

- Docker default: `/app/evidence`.
- Local/CI default: `./evidence`.
- CI should set `EVIDENCE_DIR` to a writable temporary directory.

The backend refuses path traversal and creates evidence directories through a centralized path helper.
