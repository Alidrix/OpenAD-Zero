# V2 RQ Progress Worker

## Objective

This brick proves the V2 progress pipeline with a safe-by-default demo worker:

1. the API enqueues a known server-side job;
2. RQ executes the job asynchronously;
3. PostgreSQL remains the source of truth for scan status, progress, steps, and events;
4. the Scan Library can resynchronize over HTTP and use WebSocket messages only as realtime hints.

## Why a demo worker exists

`run_demo_scan(scan_id)` intentionally simulates progress only. It does not run NetExec, Nmap, shell commands, password spraying, dumps, or any offensive workflow. The frontend never sends a raw command or target to this endpoint.

## Flow

- `POST /api/v2/scans/{scan_id}/enqueue-demo` validates the scan and enqueues `run_demo_scan(scan_id)` into the `openadzero-scans` RQ queue.
- The API stores `rq_job_id`, sets the scan to `queued`, and writes `scan.queued`.
- The worker opens its own `SessionLocal`, sets `running`, writes progress events and scan steps at 0/20/40/60/80/100, then sets `completed`.
- Events are persisted in `scan_events` and can be replayed through `/ws/v2/scans/{scan_id}?replay=true`.
- The frontend polls lightly every two seconds while scans are `queued`, `running`, or `stopping` so WebSocket delivery is never required for correctness.

## Endpoints

- `GET /api/v2/scans`
- `POST /api/v2/scans`
- `GET /api/v2/scans/{scan_id}`
- `POST /api/v2/scans/{scan_id}/enqueue-demo`
- `POST /api/v2/scans/{scan_id}/stop`
- `GET /api/v2/scans/{scan_id}/events`
- `GET /api/v2/scans/{scan_id}/artifacts`
- `WS /ws/v2/scans/{scan_id}?replay=true`

## Status and stop/cancel behavior

- `queued`: a pending RQ job can be canceled with `job.cancel()` and the scan becomes `stopped`.
- `running`/`started`: the API sends `send_stop_job_command()` and the scan becomes `stopping`.
- `finished`: the scan is synchronized to `completed`.
- `failed`: the scan is synchronized to `failed`.
- `stopped`/`canceled`: the scan is synchronized to `stopped`.
- If Redis/RQ is unavailable, PostgreSQL data is not overwritten; `scan.stop_failed` is written and the API returns a clean service error.

## Known limits

The synchronous RQ worker does not force a cross-event-loop WebSocket broadcast. Persistence is the guarantee. The frontend polling fallback keeps the UI current while scans are active, and a later brick can add a dedicated Redis pub/sub bridge for worker-originated realtime messages.

## Safety reminder

This worker is a demo progress worker only. It adds no offensive catalog, no NetExec command, no raw frontend command input, no shell execution, no brute force, no password spraying, and no dump workflow.

## Recommended next step

Build the V2 dashboard aesthetics and then introduce a reviewed catalog of safe server-side templates.
## Dashboard V2 gate

The RQ progress worker consolidation is the gate for the experimental `/v2-dashboard` page. The dashboard reads existing scan list endpoints only and does not enqueue work, execute tools, or send raw commands.
