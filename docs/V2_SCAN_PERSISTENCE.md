# V2 scan persistence foundation

This first V2 backend slice adds durable scan state without changing the V1 GUI or tool automation workflows.

## Goal

OpenAD-Zero now has a PostgreSQL-backed scan model that can survive browser refreshes and theme changes. This foundation is intentionally orchestration-only: it does not launch tools, does not add NetExec automation, and does not allow a frontend to submit raw commands.

## Data model summary

- `missions`: existing mission table, extended with optional V2 metadata (`client_name`, `scope`, `updated_at`).
- `scans`: durable scan state, including type, optional tool name, status, progress, current step, optional RQ job id, lifecycle timestamps, rename timestamp, and soft-delete timestamp.
- `scan_steps`: ordered scan step progress records.
- `scan_events`: append-only timeline events for scan lifecycle changes.
- `scan_artifacts`: artifact metadata for files that must remain under `EVIDENCE_DIR`.

## Scan statuses

Allowed scan statuses are:

- `draft`
- `queued`
- `running`
- `stopping`
- `stopped`
- `completed`
- `failed`
- `deleted`

Allowed scan step statuses are `pending`, `running`, `completed`, `failed`, and `skipped`.

Progress percentages are constrained to `0..100` at both service and database levels.

## API endpoints

The new versioned API is mounted under `/api/v2/scans`:

- `POST /api/v2/scans`
- `GET /api/v2/scans`
- `GET /api/v2/scans?include_deleted=true`
- `GET /api/v2/scans/{scan_id}`
- `PATCH /api/v2/scans/{scan_id}/rename`
- `POST /api/v2/scans/{scan_id}/stop`
- `DELETE /api/v2/scans/{scan_id}`
- `GET /api/v2/scans/{scan_id}/events`
- `GET /api/v2/scans/{scan_id}/artifacts`

`POST /api/v2/scans` creates a scan in `draft` state. This is the safest default because no tool execution is implied; a future human-approved workflow can explicitly promote a scan to `queued`.

## Persistence rules

- PostgreSQL is the source of truth for V2 scan state.
- The frontend must never be the source of truth for scan state; React state or `localStorage` may only cache/display server state.
- Deletion is soft-delete only (`deleted_at` plus `status=deleted`).
- Deleted scans are excluded from list results by default.
- Rename updates `renamed_at` and writes a scan event instead of rewriting history.
- Artifact records must point under `EVIDENCE_DIR`.

## Next recommended step

Add WebSocket progress streaming and a frontend Scan Library that reads from `/api/v2/scans` instead of keeping critical scan state in the browser.
