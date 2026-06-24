# Development

## Structure

- `backend/`: FastAPI, SQLAlchemy models, RQ worker, Alembic migrations.
- `frontend/`: React, TypeScript, Vite, Tailwind.
- `scripts/`: migration, reset, seed, and smoke helpers.

## Backend

```bash
cd backend
pytest
```

## Frontend

```bash
cd frontend
npm run build
```

## Worker

The worker runs `python -m app.worker` and has a Docker healthcheck using `python -m app.healthcheck_worker`.

## Seed data

Seed data is explicit only:

```bash
make seed-dev
```
