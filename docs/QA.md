# QA Guide

## Local quick check

```bash
make up-build
make migrate
make seed-demo
make smoke
```

## Backend tests

```bash
make backend-test
```

## Frontend build

```bash
make frontend-build
```

## E2E tests

```bash
make e2e
```

## Debug Playwright

```bash
make e2e-ui
make e2e-report
```

## Demo scenario

Open the seeded mission and verify:
- Dashboard
- Hosts
- Findings
- Evidence
- Report
- Lab Operations
- Timeline
- Capabilities
- Settings

## Release checklist

- backend tests pass
- frontend build passes
- e2e pass
- smoke pass
- README up to date
- capabilities up to date
- migrations applied
