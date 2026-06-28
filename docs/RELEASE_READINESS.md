# OpenAD Zero v0.1.0-rc1 Release Readiness

## Version

- Version: 0.1.0-rc1
- Tag target: v0.1.0-rc1
- Release type: GitHub pre-release

## Validation commands

```bash
make backend-lint
make backend-format-check
make backend-test
make frontend-build
make security-check
make smoke
make e2e
make qa
make release-check
```

## CI checks

* [ ] Backend lint
* [ ] Backend format check
* [ ] Backend tests
* [ ] Frontend build
* [ ] Docker smoke
* [ ] E2E smoke
* [ ] Dependency review
* [ ] CodeQL

## Docker checks

* [ ] docker compose up --build
* [ ] API health
* [ ] DB health
* [ ] Redis health
* [ ] Worker health
* [ ] Frontend reachable

## Security checks

* [ ] No secrets committed
* [ ] No frontend exposure of DATABASE_URL / REDIS_URL / BLOODHOUND_API_TOKEN
* [ ] Evidence paths constrained under EVIDENCE_DIR
* [ ] Uploaded evidence is not executed
* [ ] No shell=True in backend/app
* [ ] Docker runtime non-root if configured
* [ ] SECURITY.md present
* [ ] CodeQL enabled
* [ ] Dependabot enabled

## Included in v0.1.0-rc1

* Mission creation.
* Scope validation.
* Nmap discovery.
* NetExec SMB safe enum.
* Nuclei safe web scan.
* BloodHound ZIP upload.
* BloodHound Explorer V1.
* Evidence Manager.
* Markdown/HTML Reporting.
* Lab Operations.
* Timeline.
* Progress Score.
* RQ worker.
* Persistent events.
* Docker Compose.
* CI / QA / release docs.

## Release decision

* [ ] Ready to tag.
* [ ] Not ready, see blockers.

## Blockers

List blockers here if any.
