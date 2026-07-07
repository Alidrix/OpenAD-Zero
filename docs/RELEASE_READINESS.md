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

## Tool execution model

OpenAD-Zero now distinguishes documented tools from runnable tools with the `executable_after_human_approval` integration status. Advanced AD/Pentest workflows such as Kerbrute, gMSADumper, DonPAPI, Coercer, BloodyAD, controlled Impacket workflows and Responder analyze mode are usable only through declared templates and explicit operator gates.

An OpenAD-Zero tool is executable only when:
1. the tool is declared in `tools.yml`;
2. the selected template is declared in `command_templates.py`;
3. the selected template is referenced by the tool;
4. the target is inside the validated scope;
5. the command preview has been generated;
6. human approval is confirmed;
7. explicit terms are accepted.

The frontend never sends a raw command to execute. The backend always rebuilds argv from an allowlisted template, refuses out-of-scope targets, refuses `0.0.0.0/0` and `::/0`, refuses public IPs by default, and keeps `manual_only`, `blocked_auto` and `planned` tools non-runnable. The GUI provides a dedicated landscape console per tool, separated terminal output and history, and a collapsible left sidebar grouped by Scope & Setup, Recon, SMB / NetExec, Active Directory, Coercion / Capture, Impacket, Credentials Review, Reports and Settings.

## Docker runtime readiness

* [ ] Backend Dockerfile copies `docker-entrypoint.sh` and uses it as `ENTRYPOINT`.
* [ ] Entrypoint repairs `/app/evidence` and `/app/runtime` permissions before dropping to `APP_UID:APP_GID`.
* [ ] API container runtime identity is UID/GID `10001:10001` after startup.
* [ ] Worker container runtime identity is UID/GID `10001:10001` after startup.
* [ ] Smoke verifies `/app/evidence` and `/app/runtime` are writable from both API and worker containers.
* [ ] Compose keeps `openadzero-evidence` and `openadzero-runtime` named volumes for default startup.

## V2 pentest orchestrator foundation

- Added a backend-only Windows/AD pentest orchestration foundation with static phases, persistent phase states, persistent action recommendation contracts, and read/recompute API endpoints.
- The foundation is intentionally non-executing: no tool launch, no RQ job creation, no subprocess usage, and no raw command acceptance.

## Prompt 04 approval readiness

- Server-side `operator_approvals` persistence and API endpoints are in place.
- Approval preparation/approval/rejection are protected by the existing API-token dependency.
- Execution remains intentionally unconnected; RQ queuing belongs to the next prompt.

## Prompt 05 strict parameter validation readiness

OpenAD-Zero now centralizes validation for network values, input files, output files, credentials, enums and free text. Tool previews, approvals and the future execution boundary use the same validator to avoid target-only scope bypasses.

- Prompt 07 adds advanced pentest decision rules with priority, dedupe keys, and recommendation-only phase updates.


## Prompt 10 readiness note

Approved action execution is available for the safe Prompt 10 template allowlist through RQ with artifacts under EVIDENCE_DIR, hash/scope revalidation, and post-run recompute. High-risk templates and broad cancel remain deferred.

## Prompt 11 Windows/AD tool catalog update

OpenAD-Zero now has a central Windows/AD tool catalogue grouped by family, risk, execution mode, parser/artifact expectations, and `supported_for_run` status. Decision rules normalize recommendations through the catalogue, approval preparation refuses manual-only/blocked templates, and approved-action run preparation remains limited to the existing Prompt 10 supported templates. The Attack Control Center includes a read-only Tool Catalog / Tool Readiness panel; it contains no run buttons.
