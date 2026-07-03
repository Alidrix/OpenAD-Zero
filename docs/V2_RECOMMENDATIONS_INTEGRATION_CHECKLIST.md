# V2 Recommendations Integration Checklist

## API checklist

- [x] Mount `routes_v2_recommendations` from `backend/app/main.py` with the `/api` prefix.
- [x] Expose `GET /api/v2/recommendations/catalog`.
- [x] Expose `GET /api/v2/scans/{scan_id}/recommendations`.
- [x] Expose `POST /api/v2/recommendations/preview`.
- [x] Return `404` for recommendations requested for an unknown scan.
- [x] Rebuild previews only from backend allowlisted template references.
- [x] Reject raw-command-like preview parameters such as `raw_command`, `command`, `argv`, and `shell`.

## Frontend checklist

- [x] Route the recommendations page at `/v2-recommendations`.
- [x] Add the sidebar link labeled `V2 Recommendations`.
- [x] Add non-executive `View recommendations` links from Scan Library rows.
- [x] Support `/v2-recommendations?scan_id=<scan_id>` preselection.
- [x] Keep recommendation actions limited to `Build preview`, `Refresh recommendations`, and `Copy preview text`.
- [x] Do not send raw commands from the frontend.

## Tests checklist

- [x] Catalog loader tests validate V2 templates, rules, and safety policy.
- [x] Recommendation engine tests validate signal-to-recommendation behavior.
- [x] Preview tests validate allowlisted template rendering and raw command rejection.
- [x] API tests validate mounted endpoints with FastAPI `TestClient`.
- [x] API tests confirm recommendation endpoints do not create jobs.
- [x] API tests confirm the recommendations router does not import `subprocess`.

## Security checklist

- [x] Recommendations remain advisory only.
- [x] Preview responses keep `executable: false`.
- [x] Preview responses keep `automatic_execution_allowed: false`.
- [x] No RQ job is created for recommendations.
- [x] No external tool is launched by recommendations.
- [x] No password spraying, dumping, lateral movement, shell, or raw command workflow is added.
