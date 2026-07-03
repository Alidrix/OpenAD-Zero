# V2 normalized scan parsing

## Objective

This slice turns already persisted V2 scan data into PostgreSQL-backed normalized rows for assets, services, lightweight findings, reusable signals, and parser diagnostics. It is parsing-only and exists to feed recommendations, dashboards, and reports without starting tools.

## Tables added

- `parsed_assets`: hosts, addresses, names, MAC and OS hints tied to `scans.id`.
- `parsed_services`: open services tied to scans and optionally parsed assets.
- `parsed_findings`: lightweight future parser findings with constrained severity.
- `parsed_signals`: compact recommendation-ready signals such as `smb_open` and `ldap_open`.
- `parse_diagnostics`: non-fatal parser warnings and informational diagnostics.

## API endpoints

- `POST /api/v2/scans/{scan_id}/parse-persisted`
- `GET /api/v2/scans/{scan_id}/parsed/assets`
- `GET /api/v2/scans/{scan_id}/parsed/services`
- `GET /api/v2/scans/{scan_id}/parsed/findings`
- `GET /api/v2/scans/{scan_id}/parsed/signals`
- `GET /api/v2/scans/{scan_id}/parsed/diagnostics`

## Generic event parser

The generic parser consumes persisted `scan_events`. It prefers structured `payload_json` keys such as `signals`, `ip`, `host`, `hostname`, `port`, `protocol`, `service`, and `os`. A narrow free-text fallback exists only for legacy events without structured payloads.

## Nmap XML parser

The Nmap XML parser reads uploaded or persisted XML artifacts already recorded in `scan_artifacts`. It uses Python standard library XML parsing, extracts hosts that are up, addresses, hostnames, open ports, service names, product/version attributes, and OS matches.

## Idempotence

The first implementation uses delete-then-reparse per scan for normalized rows only. Source `scans`, `scan_events`, and `scan_artifacts` are never deleted or modified by parsing.

## Non-fatal diagnostics

Malformed XML, missing artifact files, unsafe artifact paths, and malformed event payloads create `parse_diagnostics` rows. One bad artifact should not fail the entire request.

## Security model

- No execution.
- No subprocess.
- No external tool launch.
- Parse persisted data only.
- PostgreSQL is the source of truth.
- Artifact files are read only when resolved under `EVIDENCE_DIR`.
- No RQ job is created for parsing.

## Recommendations integration

The V2 recommendation engine reads `parsed_signals` first when they exist for a scan. If no parsed signals are available, the previous event/artifact fallback remains active.

## Known limits

- Findings are modeled but not heavily populated in this first parser slice.
- The Nmap parser intentionally supports XML artifacts only.
- Delete-then-reparse is simple and deterministic but may be replaced by controlled upserts later.

## Next steps

Add more artifact parsers for already captured safe outputs, surface parsed data in dashboard/report summaries, and add richer finding derivation while preserving the no-execution model.

## Dashboard integration

Normalized parsing feeds the V2 dashboard through the read-only `GET /api/v2/dashboard/summary` endpoint. The summary aggregates parsed assets, services, findings, signals, diagnostics, service distributions, and AD surface hints without triggering parsing, RQ jobs, subprocesses, or external tools. If parsed tables are empty, dashboard counters return zero values.
