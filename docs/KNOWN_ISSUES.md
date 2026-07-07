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
