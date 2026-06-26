# Docker

## Services

Default startup includes API, UI, PostgreSQL, Redis, and worker. BloodHound services are only in the `bloodhound` profile.

## Healthchecks

- Postgres: `pg_isready`.
- Redis: `redis-cli ping`.
- API: `/api/health`.
- Worker: `python -m app.healthcheck_worker`.
- UI: HTTP check on port 5173.

## Volumes

- `postgres-data`: OpenAD Zero database.
- `./evidence:/app/evidence`: mission evidence for API and worker.
- `bloodhound-postgres-data`: optional BloodHound database.
- `bloodhound-neo4j-data`: optional BloodHound graph storage.

## Profiles

```bash
docker compose up --build
docker compose --profile bloodhound up --build
```

## Version file

The backend reads `VERSION` when available and otherwise falls back to `0.1.0-rc1`. The current backend Docker build context is `./backend`, so the image uses the fallback unless the build context is expanded in a future Docker packaging change.

## NetExec Docker build requirements

NetExec is installed via pipx from its GitHub repository. Some dependencies, such as aardwolf, may require a Rust toolchain and native build tools when no compatible wheel is available.

The backend image therefore includes:

- rustc
- cargo
- build-essential
- python3-dev
- pkg-config
