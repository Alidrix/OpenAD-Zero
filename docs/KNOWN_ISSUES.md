# Known Issues

## v0.1.0-rc1

### BloodHound CE optional configuration

BloodHound CE requires external configuration and is not required for standard OpenAD Zero startup.

### No PDF export

Only Markdown and HTML reporting are included in this release candidate.

### No multi-user authentication

This release candidate is designed for local or controlled use.

### E2E prerequisites

E2E tests require the frontend and API stack to be reachable.

### Tool availability

Nmap, NetExec and Nuclei availability depends on the backend Docker image or local environment.

### Release candidate status

This is not a stable v1.0 release. It is intended for controlled validation.

## Tailwind CSS v4 migration

OpenAD Zero v0.1.0-rc1 intentionally stays on Tailwind CSS v3.4.17.

Tailwind CSS v4 changes the PostCSS integration and requires a dedicated migration. This migration is deferred to v0.2.0 to keep the release candidate stable.

## Docker runtime user model

The backend image intentionally starts its entrypoint as root so Docker named volumes mounted at `/app/evidence` and `/app/runtime` can be created and repaired. The entrypoint then drops privileges to `APP_UID:APP_GID` (default `10001:10001`) before launching the API or worker. Do not add a static `USER openadzero` instruction unless the volume repair flow is redesigned.

## V2 pentest orchestrator limitations

- The pentest orchestrator currently recommends actions only. Server-side approvals, RQ execution, frontend Attack Control Center integration, and `Approve & Run` wiring are intentionally deferred to later prompts.

## Approval execution not yet wired

Operator approvals can be prepared, approved, rejected, expired, and marked consumed by service code, but no RQ execution consumes approvals yet. This is intentional for Prompt 04 and should be addressed in Prompt 05.

## Prompt 05 remaining execution boundary

Strict parameter validation is in place for previews and approvals. RQ execution is still intentionally deferred; Prompt 06 should consume approved approvals atomically and reuse the same validator at job start.

- Prompt 07 does not execute recommended actions; GUI approval and RQ execution are intentionally deferred to later prompts.

## V2 Attack Control Center limitations

- `Approve & Run` is visible but disabled until the final RQ execution workflow is connected.
- V2 report generation is disabled in the cockpit until a scan-specific endpoint is confirmed.

## V2 approval execution deferred

Prompt 09 adds the approval `/run` contract, but it intentionally returns `ready: false` and does not launch RQ execution. Prompt 10 must implement the runner, consumed transitions, and queued/running action updates.


## Prompt 10 remaining limits

Only the initial safe approved-action template allowlist is executable. Unsupported approved templates return 501 without consuming the approval. Dedicated approval cancel is not yet implemented.

## Prompt 11 Windows/AD tool catalog update

OpenAD-Zero now has a central Windows/AD tool catalogue grouped by family, risk, execution mode, parser/artifact expectations, and `supported_for_run` status. Decision rules normalize recommendations through the catalogue, approval preparation refuses manual-only/blocked templates, and approved-action run preparation remains limited to the existing Prompt 10 supported templates. The Attack Control Center includes a read-only Tool Catalog / Tool Readiness panel; it contains no run buttons.


## Prompt 12 normalization update

V2 artifact outputs now flow through `backend/app/normalization/` where supported Nmap, Nuclei, NetExec SMB, BloodHound ZIP, LDAP, Kerberos, and ADCS artifacts are converted into common parsed tables. This remains parsing-only: no extra tool launch, no new RQ job creation, and no subprocess is introduced by normalization.

## Prompt 13 remaining runtime limitations

Queued cancellation is supported by existing job APIs, but cooperative live cancellation of an already running external process is limited to runner timeout/error cleanup. Prompt 14 should add a shared cancellation registry for immediate operator stop requests.

## Prompt 14 high-risk execution policy

OpenAD-Zero now uses `backend/app/tool_catalog/high_risk_policy.py` as the central policy for sensitive tooling. Metasploit is locked to preview-only/read-only entries, while credential dumping, spraying/brute force, active relay/coercion capture, command execution, lateral movement, AD write operations, exploitation, persistence, and trace cleanup remain manual-only or blocked. Approval preparation and run preparation both enforce the same policy; refused high-risk runs do not consume approvals or enqueue RQ jobs. The Attack Control Center surfaces `preview_only`, `manual_only`, and `blocked` states and does not provide a force-run path.
