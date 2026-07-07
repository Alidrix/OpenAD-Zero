# V2 server-side operator approval workflow

OpenAD-Zero uses server-side approvals so a browser pop-up can never become the source of truth for pentest execution. The frontend may ask the backend to prepare, approve, reject, or read an approval, but it never sends a raw command, argv, shell flag, command preview, or command hash.

## Why server approvals exist

A frontend confirmation only proves that a UI event occurred. A server approval records what the backend reconstructed from allowlisted tool and template metadata, what scope was in effect, which inputs were resolved, what was missing, when the approval expires, and which operator approved or rejected it.

## Lifecycle

- `pending`: created by the backend and awaiting an operator decision.
- `approved`: an operator approved the exact server-side preview/hash.
- `rejected`: an operator rejected the action and the action history is retained.
- `expired`: the pending approval exceeded `OPENADZERO_APPROVAL_TTL_SECONDS`.
- `consumed`: reserved for the future execution step after a job uses the approval once.
- `blocked`: reserved for workflows that are represented for audit but cannot be approved.

## Approval levels

- `standard`: used for `safe_auto` and `approval_required` actions. Approval is still explicit.
- `reinforced`: used for `reinforced_approval_required` actions and requires a non-empty confirmation string.
- `manual_only_blocked`: manual-only workflows cannot become approved or queued by OpenAD-Zero.

## TTL and expiration

The default TTL is 900 seconds. Pending approvals are checked for expiration when they are read or acted on. Expired, rejected, consumed, and blocked approvals cannot be approved.

## Server hash and masked preview

The backend rebuilds the argv preview from the action `tool_id`, `template_id`, and stored resolved inputs. It masks credential-like fields, stores a masked preview, and hashes a canonical JSON payload containing tool id, template id, rendered argv, masked resolved inputs, scope snapshot, risk level, and approval level.

## No raw command input

Approval request schemas forbid extra fields, so frontend payloads containing `command`, `argv`, `shell`, `command_preview`, or `command_hash` are rejected before service logic runs.

## Future Prompt 05

Prompt 05 can wire approved `approval_id` records to RQ execution. That next step should consume the approval atomically and reject any attempt to reuse it.

## Prompt 05 parameter validation

Approval preparation now validates all template-declared network, file input, file output, credential, enum and free-text parameters before creating a pending approval. The scope snapshot includes validated scope values, and approval cannot be prepared for out-of-scope network parameters or filesystem paths outside evidence/runtime roots.

## Decision-rule approval posture

Prompt 07 recommendations classify high-risk or reinforced actions as waiting for approval. Manual-only actions remain blocked. No Approve & Run execution is wired in this prompt.


## Prompt 10 execution update

Approved approvals can now be queued through `POST /api/v2/approvals/{approval_id}/run`. The endpoint accepts only `operator` and optional `operator_note`, rebuilds argv server-side, revalidates the command hash and scope, and consumes the approval only after a stable RQ job is created.
