# V2 Dashboard Mission Control

## Objective

The V2 Dashboard Mission Control page is a minimal read-only overview for persisted V2 scan operations. It consolidates scan counters, active scan progress, and recent scan visibility without adding any execution workflow.

## Prerequisites

This dashboard is gated behind the V2 RQ consolidation:

- `POST /api/v2/scans/{scan_id}/enqueue-demo` is available for safe demo progress only.
- The RQ worker persists progress in PostgreSQL.
- The Scan Library can resynchronize over HTTP and uses WebSocket only as a realtime hint.
- Backend V2 tests and the frontend build pass before relying on this page.

## Endpoints used

The dashboard reads existing APIs only:

- `GET /api/v2/scans`
- `GET /api/v2/scans?include_deleted=true`

No new backend endpoint is required for this first dashboard slice.

## Frontend components added

- `frontend/src/pages/V2DashboardPage.tsx`
  - orbital counter cards
  - active scans panel
  - recent scans panel
  - safety banner
  - two-second HTTP polling while scans are `queued`, `running`, or `stopping`
- Route: `/v2-dashboard`
- Sidebar link: `V2 Dashboard`

## Design palette

The page uses a restrained retro-spatial palette inspired by warm metallic orange, soft gray, off-white, and clean white surfaces:

- background: `#FAF9F5`
- surface: `#FFFFFF`
- text-primary: `#141413`
- text-secondary: `#6F6B63`
- border: `#E8E6DC`
- soft-gray: `#B1ADA1`
- orange: `#C15F3C`
- orange-light: `#F28A4B`
- orange-dark: `#8E3E26`

## Safety rule

Dashboard V2 is read-only visualization. It does not create scans, enqueue work, send raw commands, call shells, or define offensive templates. PostgreSQL remains the source of truth, Redis/RQ remains asynchronous execution plumbing, and WebSocket remains realtime-only.

## Next steps

- Define the final visual identity and logo.
- Add a safe template catalog when the safety model is ready.
- Add recommendations based on parsed results, without introducing offensive automation.

## Frontend hardening update

The dashboard is reachable at `/v2-dashboard` and remains read-only. It imports the shared V2 tokens from `frontend/src/styles/v2-theme.css`, uses two-second polling only while a scan is active, and links back to `/scans` for inspection instead of exposing run controls.

## V2 brand identity update

The dashboard now presents the V2 product identity as **AD Mission Control** with the tagline **Persistent Active Directory audit operations**. It remains read-only: it lists counters, active scans, recent scans, Mission Control status, and persistence guarantees, but it does not enqueue demo work or execute tools.

## V2 recommendations preview link

A separate `/v2-recommendations` page now provides preview-only recommendations derived from persisted V2 scan data. Mission Control remains read-only and does not execute recommendations, enqueue recommendation jobs, or accept raw commands.

## Parsed Intelligence summary

The V2 dashboard now consumes `GET /api/v2/dashboard/summary` to display normalized parsed assets, services, signals, diagnostics, top services, and AD surface hints. The dashboard remains read-only: it does not enqueue jobs, trigger parsing, execute tools, create subprocesses, or launch external binaries. Parsing is still only available from `/v2-parsed-data` against persisted scan data.

## Parsed Intelligence consolidation

- The backend dashboard router is mounted in FastAPI, exposing `GET /api/v2/dashboard/summary` under the `/api` prefix.
- The V2 dashboard frontend uses `getV2DashboardSummary()` instead of deriving parsed metrics from scan lists alone.
- `/v2-parsed-data` is available from React routing and from the sidebar as **V2 Parsed Data**.
- Dashboard actions remain read-only: refresh only re-reads PostgreSQL through backend APIs.
- The dashboard does not parse persisted data, enqueue jobs, create subprocesses, launch external tools, or run recommendation previews.
