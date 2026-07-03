# V2 Dashboard Parsed Intelligence Checklist

## Backend

- [x] `routes_v2_dashboard` is imported by `backend/app/main.py`.
- [x] Dashboard router is mounted with `app.include_router(v2_dashboard_router, prefix="/api")`.
- [x] `GET /api/v2/dashboard/summary` supports `include_deleted`, `scan_id`, and `limit_recent`.
- [x] Missing `scan_id` returns 404.
- [x] Summary includes scan counters, parsed counters, signal counters, asset counters, AD surface counters, top services, recent scans, and recent diagnostics.

## Frontend

- [x] `frontend/src/lib/v2DashboardApi.ts` exposes `getV2DashboardSummary()`.
- [x] `/v2-dashboard` uses the summary endpoint as the primary data source.
- [x] `/v2-parsed-data` is routed.
- [x] Sidebar contains **V2 Parsed Data**.
- [x] Scan Library and Recommendations provide navigation links to parsed data without triggering actions.

## Tests

- [x] Dashboard summary returns 200.
- [x] Empty parsed data returns zero counters.
- [x] Parsed assets, services, LDAP signals, Kerberos signals, SMB surface, scan filtering, missing scans, recent limits, and deleted-scan inclusion/exclusion are covered.
- [x] Dashboard summary verifies no subprocess call and no RQ job creation.

## Safety

- [x] Dashboard is read-only.
- [x] No parsing from dashboard.
- [x] No RQ job from dashboard.
- [x] No subprocess.
- [x] No external tool launch.
- [x] PostgreSQL is the source of truth.
