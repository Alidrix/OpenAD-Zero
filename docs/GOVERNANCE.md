# OpenAD Zero Governance

## Project scope

OpenAD Zero is a safe-by-default Active Directory lab operations platform for authorized internal labs, CTFs, training environments and controlled assessment workflows.

## Release model

The project uses release candidate tags for early public milestones.

Current release candidate:

- v0.1.0-rc1

## Branch model

- main: stable development branch.
- feature branches: short-lived implementation branches.
- release tags: immutable release points.

## Pull request expectations

Every pull request should:

- describe the change;
- explain safety impact;
- pass CI;
- update tests when needed;
- update documentation when behavior changes;
- avoid adding arbitrary shell execution;
- avoid exposing secrets to the frontend.

## Security-sensitive changes

Changes in these areas require careful review:

- backend/app/core;
- backend/app/jobs;
- backend/app/api;
- backend/app/integrations;
- backend/app/evidence;
- backend/app/queue;
- backend/Dockerfile;
- docker-compose.yml;
- GitHub Actions workflows;
- scripts/security-check.sh.
