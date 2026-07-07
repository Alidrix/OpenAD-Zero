# V2 approved action execution

## Objective

`POST /api/v2/approvals/{approval_id}/run` now queues a strictly controlled RQ execution for a server-approved action. The frontend sends only `operator` and optional `operator_note`; the backend rebuilds argv from the allowlisted template catalog.

## Preconditions and lifecycle

1. A V2 pentest action is prepared for approval.
2. The operator approves the latest pending approval.
3. `/run` reloads the approval/action/scan, rejects incompatible states, revalidates TTL, scope, file parameters, and the canonical server command hash.
4. After RQ enqueue succeeds, the approval is marked `consumed`, the action is marked `queued`, and an `approved_action_runs` record stores the RQ id and masked command metadata.
5. The worker marks the action `running`, writes artifacts under `EVIDENCE_DIR/approved-actions/{approval_id}`, executes with `shell=False`, then marks `completed`, `failed`, or `timeout`.

## Supported templates in Prompt 10

Only low-risk/safe templates are executable:

- `nmap_safe_discovery`
- `netexec_smb_fingerprint`
- `netexec_smb_signing_check`
- `netexec_smb_null_session_check`
- `netexec_smb_null_session_shares`
- `nuclei_safe_templates`
- `nuclei_web_exposure_scan`

High-risk workflows such as Impacket sensitive modules, Kerbrute/password spray, DonPAPI, Coercer, Responder capture, Metasploit exploitation, BloodyAD writes, Mimikatz, secretsdump, xp_cmdshell, and remote command execution remain disabled. Unsupported templates return `501 Template not executable yet` without consuming the approval.

## Hash and scope safety

The run path reconstructs the masked preview and canonical approval hash from server state and refuses mismatches. Parameter validation is repeated before enqueue and again in the worker with file input/output controls rooted in `EVIDENCE_DIR` or runtime-approved locations.

## RQ and artifacts

Jobs are queued on `openadzero-actions` with stable RQ id `approval-run:{approval_id}` and settings:

- `OPENADZERO_ACTION_JOB_TIMEOUT_SECONDS`
- `OPENADZERO_ACTION_JOB_TTL_SECONDS`
- `OPENADZERO_ACTION_RESULT_TTL_SECONDS`

Artifacts include `command.masked.json`, `stdout.log`, `stderr.log`, and `metadata.json`.

## Parsing and recompute

Completed runs parse NetExec SMB signals/findings and Nuclei JSONL findings when possible. Missing or empty parser results create diagnostics instead of failing the job. Successful completion triggers `PentestOrchestrator.recompute(scan_id)`.

## Events

The backend records events such as `approval.run_requested`, `approval.run_queued`, `approved_action.running`, `approved_action.completed`, `approved_action.failed`, `approved_action.timeout`, `approved_action.parsing_started`, `approved_action.parsing_completed`, and `approved_action.recompute_completed`. Payloads contain ids, statuses, RQ ids, and artifact metadata only; secrets and raw credentials are not emitted.

## Limits

Cancel remains limited to existing scan/job stop capabilities; a dedicated approval cancel API is deferred. Prompt 10 intentionally does not activate all tools or high-risk execution templates.

## Prompt 11 Windows/AD tool catalog update

OpenAD-Zero now has a central Windows/AD tool catalogue grouped by family, risk, execution mode, parser/artifact expectations, and `supported_for_run` status. Decision rules normalize recommendations through the catalogue, approval preparation refuses manual-only/blocked templates, and approved-action run preparation remains limited to the existing Prompt 10 supported templates. The Attack Control Center includes a read-only Tool Catalog / Tool Readiness panel; it contains no run buttons.
