# Release Candidate Guide

## Goal

This document describes the checks required before tagging an OpenAD Zero release candidate.

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

* Backend containers must run as non-root.
* No secret must be exposed in frontend/src.
* Only `VITE_*` variables are visible to client-side Vite code.
* Backend-only secrets such as `BLOODHOUND_API_TOKEN`, `DATABASE_URL` and `REDIS_URL` must never be referenced in frontend/src.
* No `.env.local` file must be committed.
* No `shell=True` is allowed in backend/app.
* Evidence paths must go through `app.core.paths`.

## Release candidate acceptance

* CI green.
* Docker smoke green.
* Backend tests green.
* Frontend build green.
* Security check green.
* README and docs updated.
