# V2 Attack Control Center

The **Attack Control Center** is the premium V2 cockpit for Windows/AD internal pentest orchestration. It consolidates scan state, pentest phase progress, discovered assets metrics, findings, recommended actions, server-side approvals, and recent activity without launching tools from the frontend.

## Main components

- `V2AttackControlCenter.tsx`: page-level scan selection, refresh, initial discovery, recompute, metrics, timeline, action queue, findings, and activity feed.
- `MetricCard`, `PhaseTimeline`, `ActionQueue`, `FindingTable`, `ActivityFeed`: reusable cockpit blocks.
- `ApprovalModal`: server approval review, prepare, reject, and approve workflow.
- `StatusBadge`, `SeverityBadge`, `ExecutionModeBadge`, `EmptyState`, `LoadingState`: reusable V2 UX primitives.
- `designSystem.ts`: V2 colors, gradients, shadows, spacing, Motion presets, and status/severity styles.

## Backend data used

The page uses existing V2 backend endpoints only:

- `GET /api/v2/scans`
- `GET /api/v2/scans/{scan_id}/events`
- `POST /api/v2/scans/{scan_id}/start-initial-discovery`
- `GET /api/v2/pentest/phases`
- `GET /api/v2/scans/{scan_id}/pentest/state`
- `GET /api/v2/scans/{scan_id}/pentest/actions`
- `POST /api/v2/scans/{scan_id}/pentest/recompute`
- `POST /api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/prepare`
- `POST /api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/approve`
- `POST /api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/reject`
- `GET /api/v2/approvals/{approval_id}`
- `GET /api/v2/scans/{scan_id}/approvals`

## Frontend auth

The V2 API helper reuses the local auth helper from Prompt 03 and attaches `Authorization: Bearer <token>` only when the operator has configured a token locally. The token is never rendered, logged, or committed in source. A `401` is displayed as `API token required` with a link to Settings.

## Initial discovery workflow

`Start initial discovery` requires a selected scan and always sends the fixed `safe_default` profile. The operator cannot provide free-form options. The button is disabled while a scan is queued, running, stopping, or deleted.

## Approval workflow

The action queue opens `ApprovalModal` for recommended actions. The modal can prepare, reject, or approve a server-side approval. Reinforced approvals require explicit confirmation text before approval. Manual-only and blocked actions cannot be approved from the UI.

## Current limitations

- `Approve & Run` is intentionally disabled until the final RQ execution workflow is implemented in a later prompt.
- The frontend never sends raw command material, argv arrays, shell strings, or command hashes.
- No 21st.dev dependency, marketplace UI dependency, external API key, or `TWENTY_FIRST_API_KEY` is used.
