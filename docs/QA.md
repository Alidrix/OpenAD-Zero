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
make backend-test
make backend-format-check
```

## Frontend

```bash
make frontend-build
make e2e
```

## Full QA

```bash
make qa
```

## Notes

* E2E tests must not launch real scans.
* Backend tests use isolated temporary evidence directories.
* Docker smoke validates API, DB, Redis, worker and frontend health.
