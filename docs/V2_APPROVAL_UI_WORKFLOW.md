# V2 Approval UI Workflow

The Attack Control Center separates a recommended action from an operator approval. A recommended action is a server-side proposal with resolved inputs, missing inputs, risk level, and execution mode. An approval is a separate server-generated record with an `approval_id`, masked preview, scope snapshot, server command hash, expiration, and status.

## Workflow

1. **Review**: the operator opens an action and sees action details, available inputs, missing inputs, risk, and execution mode.
2. **Prepare approval**: the frontend calls the prepare endpoint. The backend rebuilds the preview from allowlisted templates and validated scope, computes the command hash, and returns the approval.
3. **Approve**: the frontend sends only `operator`, optional `operator_note`, and required `reinforced_confirmation` for reinforced approvals.
4. **Reject**: the frontend sends only `operator` and `reason`.
5. **Expired**: expired approvals cannot be approved. The UI offers preparing a new approval.
6. **Future run**: `Approve & Run` remains non-executing until Prompt 10.

## Endpoints

- `POST /api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/prepare`
- `POST /api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/approve`
- `POST /api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/reject`
- `GET /api/v2/approvals/{approval_id}`
- `GET /api/v2/scans/{scan_id}/approvals`
- `GET /api/v2/scans/{scan_id}/approvals/summary`
- `POST /api/v2/approvals/{approval_id}/run`

The `/run` endpoint is contractual only in Prompt 09. It verifies the approval and action state, then returns `ready: false` with a message explaining that the execution runner will be enabled in Prompt 10. It does not enqueue RQ jobs, mark approvals consumed, or move actions to queued/running.

## UI statuses

- `pending`: approve and reject are available.
- `approved`: displayed as approved and ready for future execution, but execution is not enabled.
- `rejected`: displays the rejection reason when present.
- `expired`: displays expiration and allows preparing a new approval.
- `consumed`: displays that the approval has already been consumed.
- `blocked`: displays the blocking reason and does not allow approval.

## Security guarantees

The frontend never builds or submits raw commands, `argv`, `shell`, `raw_command`, `command_hash`, or `human_approved`. The backend computes the command hash from server-side state, returns only a masked preview, requires API authentication through the existing V2 router protection, validates scope-sensitive parameters, and persists only UI-safe approval events.


## Prompt 10 Approve & Run update

The Attack Control Center now enables **Approve & Run** for approved, unconsumed approvals. The UI calls `/api/v2/approvals/{approval_id}/run` without command, argv, shell, or hash fields and refreshes server state after the queued response. A `501` response is shown as “Template not executable yet”.
