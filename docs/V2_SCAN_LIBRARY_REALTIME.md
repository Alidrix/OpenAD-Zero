# OpenAD-Zero V2 Scan Library + realtime

## Objective

This second V2 brick adds a reliable frontend Scan Library and a scan-specific realtime WebSocket channel without changing the safe-by-default execution model.

No offensive workflow is introduced here: the UI only lists and controls already persisted V2 scans through the V2 HTTP API.

## HTTP endpoints used

The Scan Library uses the existing V2 scan endpoints:

- `GET /api/v2/scans`
- `GET /api/v2/scans?include_deleted=true`
- `GET /api/v2/scans/{scan_id}`
- `PATCH /api/v2/scans/{scan_id}/rename`
- `POST /api/v2/scans/{scan_id}/stop`
- `DELETE /api/v2/scans/{scan_id}`
- `GET /api/v2/scans/{scan_id}/events`
- `GET /api/v2/scans/{scan_id}/artifacts`

## WebSocket endpoint

A scan-specific WebSocket endpoint is available at:

```text
/ws/v2/scans/{scan_id}
```

Use `?replay=true` to replay persisted `scan_events` in creation order before keeping the socket open:

```text
/ws/v2/scans/{scan_id}?replay=true
```

Messages include the event type, scan id, status/progress/current step when available, message, payload, and timestamp.

## Persistence and resynchronization rules

PostgreSQL remains the source of truth. The WebSocket is only a realtime notification channel.

If the WebSocket disconnects or the browser refreshes, the frontend resynchronizes through HTTP by calling `GET /api/v2/scans` and, for inspection, `GET /api/v2/scans/{scan_id}/events` plus `GET /api/v2/scans/{scan_id}/artifacts`.

## Browser refresh behavior

The Scan Library does not initialize scan data from React-only state or `localStorage`. It fetches scans from `/api/v2/scans` on load, so a browser refresh does not delete or hide persisted scans.

## Theme behavior

Dark/light theme state is treated as a UI preference only. Changing theme must not clear scans, call delete endpoints, or make `localStorage` a source of scan truth. The Scan Library can always reload persisted scans from the API.

## Known limits

- Realtime broadcast is best-effort: if broadcasting fails, the HTTP mutation still succeeds after persistence.
- The demo pipeline includes RQ enqueue and API-side stop/cancel synchronization; cooperative in-loop stop handling inside the demo worker is still a known future hardening item.
- This step does not add any NetExec workflow, command catalog, or offensive automation.
- The UI is intentionally minimal and stable; the final V2 dashboard visual redesign is deferred.

## Recommended next step

Integrate real RQ scan workers that emit persisted progress events, add robust worker cancellation semantics, then build the final aesthetic V2 dashboard on top of the same persisted scan model.

## RQ demo progress hardening

The Scan Library now includes a temporary **Run demo progress** action that calls `POST /api/v2/scans/{scan_id}/enqueue-demo`. The action validates the worker-to-PostgreSQL progression path without launching external tools. During active states (`queued`, `running`, `stopping`), the frontend performs a light two-second HTTP refresh so WebSocket messages remain realtime hints rather than the source of truth.
