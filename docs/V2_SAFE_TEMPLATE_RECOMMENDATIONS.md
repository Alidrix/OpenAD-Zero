# V2 Safe Template Recommendations

## Objective

This slice adds the first safe-by-default V2 recommendation layer. It reads scan metadata, persisted events, and persisted artifacts, then proposes consultative next steps as command previews only.

## Metadata-only catalog

The catalog lives under `command-catalog/v2/`:

- `templates.safe.yml` describes V2 safe templates and references existing backend allowlisted `template_ref` identifiers.
- `recommendation_rules.yml` maps simple scan signals to recommendation reasons and priorities.
- `safety_policy.yml` states the non-execution policy for this slice.

The V2 catalog does not contain free-form raw commands and does not launch tools.

## Safety policy

The default policy requires scope validation, backend template rebuild, raw frontend command rejection, and human approval for previews. Automatic execution, public targets, global CIDRs, NetExec execution, and external tool execution are disabled for this slice.

Blocked categories include exploitation, credential dumping, password spraying, brute force, command execution, lateral movement, coercion execution, file writes, persistence, and privilege escalation.

## Recommendation rules

Initial signals are intentionally simple: discovered hosts, Windows host hints, SMB/LDAP/Kerberos/HTTP service hints, completed scans, uploaded artifacts, and BloodHound-style artifacts. Rules produce explanations and priorities only; they do not enqueue jobs or call subprocesses.

## API endpoints

- `GET /api/v2/recommendations/catalog` returns the metadata catalog, rules, and simplified safety policy.
- `GET /api/v2/scans/{scan_id}/recommendations` reads PostgreSQL-backed scan state, events, and artifacts, then returns matching recommendations.
- `POST /api/v2/recommendations/preview` accepts a `template_id` plus parameter values and returns an argv preview rebuilt by the backend.

## Frontend page

`/v2-recommendations` presents a safety banner, catalog panel, scan recommendation panel, and command preview panel. The page offers `Build preview`, `Refresh recommendations`, and optional `Copy preview text` actions only.

## Preview behavior

The frontend never sends a raw command. The backend resolves the V2 template, checks that the referenced template exists in the existing command-template allowlist, rejects raw-command-like fields, validates expected parameters, and returns `executable: false` with `automatic_execution_allowed: false`.

## Hard rules in this slice

- Backend rebuilds argv from allowlisted templates.
- No raw frontend commands are accepted.
- No automatic execution is created.
- No NetExec execution is added in this slice.
- No RQ job is created by recommendations or previews.
- Uploaded/imported artifacts remain review-only and are never executed.

## Known limits

Signals are currently heuristic and derived from persisted scan fields, event messages/payloads, and artifact metadata. The engine does not yet parse rich scanner output into normalized service entities.

## Next steps

Add richer normalized service/artifact signals, introduce operator-facing approval records for future safe assisted flows, and keep high-risk templates gated as documentation-only until a separate safety review approves any execution path.

## Integration status

- The FastAPI recommendations router is mounted from `backend/app/main.py` with the `/api` prefix.
- The frontend recommendations page is routed at `/v2-recommendations`.
- The sidebar includes a `V2 Recommendations` navigation link.
- Scan Library rows include a non-executive `View recommendations` link to `/v2-recommendations?scan_id=<scan_id>`.
- The mounted endpoints are covered by API tests:
  - `GET /api/v2/recommendations/catalog`
  - `GET /api/v2/scans/{scan_id}/recommendations`
  - `POST /api/v2/recommendations/preview`
- Previews are still preview-only and return `executable: false`.
- Automatic execution remains disabled and previews return `automatic_execution_allowed: false`.
- The frontend does not send raw commands.
- The backend rebuilds argv previews from allowlisted templates and rejects raw-command-like parameters.

## Parsed signals integration

V2 recommendations now prefer normalized `parsed_signals` produced by the persisted-data parser when available for a scan. If a scan has no parsed signals, the previous persisted scan/event/artifact fallback remains in place.
