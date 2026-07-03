# V2 Dashboard Parsed Intelligence

## Objective

The V2 dashboard now exposes a read-only parsed-intelligence summary for persisted scan data. It consolidates normalized `parsed_assets`, `parsed_services`, `parsed_findings`, `parsed_signals`, and `parse_diagnostics` into one API response so the frontend does not need to fan out across every parsing endpoint.

## Endpoint

`GET /api/v2/dashboard/summary`

Optional query parameters:

- `include_deleted=false` includes soft-deleted scans when set to `true`.
- `scan_id=<id>` limits parsed metrics to one persisted scan and returns `404` when the scan does not exist.
- `limit_recent=5` controls the number of recent scans and recent diagnostics returned.

## Metrics exposed

The response contains:

- scan counters: total, active, queued, running, completed, failed, stopped, deleted;
- parsed row counters: assets, services, findings, signals, diagnostics;
- signal counters: `smb_open`, `ldap_open`, `kerberos_open`, `http_open`, `rdp_open`, `winrm_open`, `mssql_open`, `ssh_open`;
- top ports and top service names from normalized services;
- asset operating-system counters;
- AD surface counters for SMB, LDAP, Kerberos, WinRM, RDP, and domain-controller hints;
- recent scans and recent parsing diagnostics.

## Read-only safety model

The dashboard summary is read-only by design:

- no execution;
- no parsing trigger from the dashboard;
- no subprocess;
- no RQ job;
- no external tool launch;
- PostgreSQL is the source of truth.

The dashboard uses only API reads against the backend summary endpoint. Parsing remains a deliberate user action on `/v2-parsed-data`, where **Parse persisted data** calls only `POST /api/v2/scans/{scan_id}/parse-persisted` against already persisted scan artifacts and events.

## Frontend usage

`/v2-dashboard` calls `getV2DashboardSummary()` from `frontend/src/lib/v2DashboardApi.ts` and renders:

- Parsed Intelligence;
- AD Surface;
- Signal Matrix;
- Top Services;
- Diagnostics panel;
- non-executive navigation links to Scan Library, Parsed Data, and Recommendations.

## Known limitations

- Domain-controller hints are heuristics based on parsed LDAP/Kerberos signals and normalized services.
- The dashboard does not automatically parse historical scans; users must visit `/v2-parsed-data` for explicit persisted-data parsing.
- If no parsed rows exist, the endpoint returns clean zero counters.

## Next steps

- Add optional per-scan parsed summary badges to the Scan Library when a lightweight endpoint exists.
- Add richer diagnostic severity grouping once parser diagnostics are more structured.
- Extend AD surface heuristics with future normalized Active Directory object parsers.

## Consolidation hardening status

- The FastAPI router `app.api.routes_v2_dashboard` is imported and mounted from `backend/app/main.py` with the `/api` prefix.
- `GET /api/v2/dashboard/summary` is the exposed dashboard summary endpoint.
- `/v2-dashboard` consumes `getV2DashboardSummary()` from `frontend/src/lib/v2DashboardApi.ts` as its primary source of parsed intelligence.
- `/v2-parsed-data` is routed in the React application and linked from the sidebar.
- The dashboard is read-only: it does not trigger parsing, enqueue RQ work, launch external tools, call subprocesses, or build recommendation previews.
- PostgreSQL-backed API responses remain the source of truth for scan counters, parsed counters, signal matrix, AD surface hints, top services, recent scans, and diagnostics.
