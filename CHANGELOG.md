# Changelog

All notable changes to OpenAD Zero will be documented in this file.

## [0.1.0-rc1] - 2026-06-26

### Added

- FastAPI backend.
- React/Vite frontend.
- PostgreSQL and Redis stack.
- RQ worker for long-running jobs.
- Persistent mission event bus.
- Nmap discovery.
- NetExec SMB safe enumeration.
- Nuclei safe web exposure scanning.
- BloodHound / SharpHound ZIP upload.
- BloodHound Explorer V1.
- Capability matrix.
- Evidence Manager.
- Reporting Engine Markdown / HTML.
- Lab Operations Center.
- Mission Timeline.
- Progress Score.
- Docker Compose healthchecks.
- Optional BloodHound CE Docker profile.
- Alembic migrations.
- QA and CI workflow.
- Security checks and release checks.

### Changed

- Evidence storage now uses a centralized safe path helper.
- Docker backend image supports Rust/Cargo build dependencies for NetExec.
- CI uses isolated temporary evidence directories.
- README and docs updated for release candidate workflow.

### Security

- Evidence paths are constrained under EVIDENCE_DIR.
- Uploaded evidence is not executed.
- Frontend does not expose backend secrets.
- Backend logging redacts sensitive values.
- Docker runtime is intended to run as non-root.
- GitHub dependency review is enabled for pull requests.

### Known limitations

- BloodHound CE is optional and must be configured separately.
- SharpHound is not executed automatically.
- No credentials are stored or used by OpenAD Zero.
- No exploitation, credential dumping, pass-the-hash, DCSync, persistence or lateral movement is automated.
- PDF export is not implemented in this release candidate.
