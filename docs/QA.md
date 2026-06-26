# QA Guide

## Local quick check

```bash
cp .env.example .env
make up-build
make migrate
make smoke
```

## Backend

```bash
make backend-lint
make backend-format-check
make backend-test
```

## Frontend

```bash
make frontend-build
make e2e
```

## Release candidate validation

```bash
make security-check
make release-check
```

## Notes

- E2E tests must not launch real scans.
- Backend tests use isolated temporary evidence directories.
- Docker smoke validates API, DB, Redis, worker and frontend health.
- Release checks require `VERSION`, `CHANGELOG.md`, release notes, and release scripts to exist.
