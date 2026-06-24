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
