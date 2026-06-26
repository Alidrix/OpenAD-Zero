# Release Candidate Guide

## Current candidate

- Version: `0.1.0-rc1`.
- Version endpoint: `GET /api/version`.
- Release notes: `docs/releases/v0.1.0-rc1.md`.
- Changelog: `CHANGELOG.md`.

## Local checks

```bash
cp .env.example .env
make up-build
make migrate
make smoke
make backend-test
make frontend-build
make security-check
make release-check
```

## Docker checks

```bash
docker compose run --rm openadzero-api id
docker compose run --rm openadzero-worker id
docker compose run --rm openadzero-api nxc --help
docker compose run --rm openadzero-api nuclei -version
```

## Security checks

- Backend containers must run as non-root.
- No secret must be exposed in `frontend/src`.
- Only `VITE_*` variables are visible to client-side Vite code.
- Backend-only secrets such as `BLOODHOUND_API_TOKEN`, `DATABASE_URL` and `REDIS_URL` must never be referenced in `frontend/src`.
- No `.env.local` file must be committed.
- No `shell=True` is allowed in `backend/app`.
- Evidence paths must go through `app.core.paths`.

## Acceptance

- CI green.
- Docker smoke green.
- Backend tests green.
- Frontend build green.
- Security check green.
- Release check green.
- README, changelog, release notes, demo guide and release checklist reviewed.
