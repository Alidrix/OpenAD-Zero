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


## Prompt 12 normalization update

V2 artifact outputs now flow through `backend/app/normalization/` where supported Nmap, Nuclei, NetExec SMB, BloodHound ZIP, LDAP, Kerberos, and ADCS artifacts are converted into common parsed tables. This remains parsing-only: no extra tool launch, no new RQ job creation, and no subprocess is introduced by normalization.

## Prompt 13 job runtime hardening

Release readiness now includes the shared process runner, bounded logs, process-group timeout cleanup, and security checks that prevent raw subprocess execution outside approved backend helpers.

## Prompt 14 high-risk execution policy

OpenAD-Zero now uses `backend/app/tool_catalog/high_risk_policy.py` as the central policy for sensitive tooling. Metasploit is locked to preview-only/read-only entries, while credential dumping, spraying/brute force, active relay/coercion capture, command execution, lateral movement, AD write operations, exploitation, persistence, and trace cleanup remain manual-only or blocked. Approval preparation and run preparation both enforce the same policy; refused high-risk runs do not consume approvals or enqueue RQ jobs. The Attack Control Center surfaces `preview_only`, `manual_only`, and `blocked` states and does not provide a force-run path.


## Prompt 15 release readiness

Alembic currently has a single effective head: `0006_add_v2_ad_normalized_models`, which merges the two prompt-14 era `0006` branches (`0006_add_approved_action_runs` and `0006_add_pentest_decision_rule_metadata`). Normal usage is `alembic upgrade head`; `upgrade heads` should not be required. Verify with `cd backend && alembic heads` and run `make migrate` before QA. The protected `/api/health/schema` endpoint reports missing required tables/columns and returns a migration hint without secrets.

## Prompt 16 final V2 QA readiness

- Added `scripts/local-e2e-qa.sh` for local Docker Compose end-to-end smoke, schema health, V2 API smoke, and frontend reachability checks.
- Added `scripts/v2-api-smoke.sh` for token-aware V2 API health/catalog/readiness checks without printing secrets.
- Added a fixture-only safe V2 backend workflow test that validates normalization, recompute, server approval, queued run, mocked runner completion, post-run normalization, recompute events, and high-risk non-execution.
- If Docker is skipped in Codex/CI with `OPENADZERO_RELEASE_CHECK_SKIP_DOCKER=1`, local Docker QA remains required using `docs/V2_FINAL_QA_RUNBOOK.md`.
