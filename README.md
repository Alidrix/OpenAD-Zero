# OpenAD Zero

OpenAD Zero is a safe-by-default Active Directory lab operations platform for authorized internal labs, CTFs, training environments, and controlled assessment workflows.

It combines a FastAPI backend, React/Vite frontend, PostgreSQL, Redis, RQ worker, evidence handling, Markdown/HTML reporting, lab operations, timeline/progress views, and an explicit capability matrix.

## Quick start

```bash
cp .env.example .env
make up-build
make migrate
make smoke
```

Then open:

- UI: http://localhost:5173
- API: http://localhost:8000
- API health: http://localhost:8000/api/health
- Version: http://localhost:8000/api/version

## Release candidate

Current version: `0.1.0-rc1`

See:

- `CHANGELOG.md`
- `docs/releases/v0.1.0-rc1.md`
- `docs/releases/github-release-draft-v0.1.0-rc1.md`
- `docs/RELEASE_CANDIDATE.md`
- `docs/RELEASE_PROCESS.md`
- `docs/DEMO.md`

## Project governance

See:

- `SECURITY.md`
- `docs/GOVERNANCE.md`
- `docs/GITHUB_PROJECT.md`
- `docs/SCOPE_MATRIX.md`
- `docs/RELEASE_PROCESS.md`
- `docs/backlog/v0.2.0.md`

## Safety model

OpenAD Zero is intentionally limited to safe orchestration and evidence workflows:

- No automatic exploitation.
- No credential dumping, LSASS dump, DCSync, pass-the-hash, persistence, or lateral movement automation.
- No arbitrary shell command from the frontend.
- Public ranges are refused by default unless explicitly configured for an authorized environment.
- Evidence paths are constrained under `EVIDENCE_DIR` and uploaded evidence is not executed.
- BloodHound / SharpHound collection is manual and optional.

## Included workflows

- Mission creation and internal scope validation.
- Nmap discovery.
- NetExec SMB safe enumeration with backend allowlists and approval controls.
- Nuclei safe web exposure scanning with local safe templates.
- BloodHound / SharpHound ZIP upload and BloodHound Explorer V1.
- Evidence Manager and Reporting Engine for Markdown/HTML reports.
- Lab Operations, Timeline, Progress Score, Settings, health checks, and capabilities.

## Common commands

```bash
make up              # start services
make up-build        # rebuild and start services
make migrate         # apply Alembic migrations inside the API container
make backend-test    # run backend tests
make frontend-build  # build frontend
make security-check  # run repository security checks
make release-check   # run release candidate validation checks
make up-bloodhound   # optional BloodHound CE profile
make version         # print the current application version
```

## Documentation

- [Install](docs/INSTALL.md)
- [Development](docs/DEV.md)
- [Docker](docs/DOCKER.md)
- [QA](docs/QA.md)
- [Demo guide](docs/DEMO.md)
- [Release candidate](docs/RELEASE_CANDIDATE.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)
- [Release process](docs/RELEASE_PROCESS.md)
- [Security policy](SECURITY.md)
- [Governance](docs/GOVERNANCE.md)
- [GitHub project setup](docs/GITHUB_PROJECT.md)
- [Scope matrix](docs/SCOPE_MATRIX.md)
- [v0.2.0 backlog](docs/backlog/v0.2.0.md)
- [BloodHound profile](docs/BLOODHOUND_PROFILE.md)
- [Migrations](docs/MIGRATIONS.md)
