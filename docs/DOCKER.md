# Docker

## Services

Default startup includes API, UI, PostgreSQL, Redis, and worker. BloodHound services are only in the `bloodhound` profile.

## Healthchecks

- Postgres: `pg_isready`
- Redis: `redis-cli ping`
- API: `/api/health`
- Worker: `python -m app.healthcheck_worker`
- UI: HTTP check on port 5173

## Volumes

- `postgres-data`: OpenAD Zero database
- `bloodhound-postgres-data`: optional BloodHound database
- `bloodhound-neo4j-data`: optional BloodHound graph storage

## Profiles

```bash
docker compose up --build
docker compose --profile bloodhound up --build
```

### NetExec Docker build requirements

NetExec is installed via pipx from its GitHub repository. Some dependencies, such as aardwolf, may require a Rust toolchain and native build tools when no compatible wheel is available.

The backend image therefore includes:

- rustc
- cargo
- build-essential
- python3-dev
- pkg-config
