# V2 Normalized Scan Parsing Plan

## Objective

Transform persisted `scan_events` and uploaded scan artifacts into normalized, queryable signals that can feed dashboards, recommendations, reports, and future review workflows without launching external tools.

## Future tables under consideration

- `parsed_assets`: normalized hosts, addresses, hostnames, operating-system hints, and source references.
- `parsed_services`: normalized services, ports, protocols, products, and source references.
- `parsed_findings`: normalized findings derived from safe parser output and uploaded artifacts.
- `parsed_signals`: compact recommendation-ready signals tied back to scans, events, artifacts, assets, or services.

## Planned parsers

- Nmap XML parser for uploaded or persisted XML artifacts.
- NetExec text/JSON output parser for already captured output artifacts.
- BloodHound imported artifact parser for already uploaded graph-related artifacts.
- Generic service detection event parser for structured `scan_events` emitted by existing V2 scan workflows.

## Rules

- Parsing only.
- No execution.
- No subprocess.
- No external tool launch.
- PostgreSQL remains the source of truth.
- Parsers consume persisted events and artifacts only.
- Parser output must keep source references for auditability.
- Parsing failures should be recorded as non-fatal diagnostics, not hidden.

## Target signals

- `host_discovered`
- `windows_host_detected`
- `smb_open`
- `ldap_open`
- `kerberos_open`
- `http_open`
- `artifact_uploaded`
- `bloodhound_artifact_present`

## Recommended next Codex step

Implement a PostgreSQL-backed normalized parsing slice with migrations, ORM models, parser service functions, and read-only API endpoints. Start with generic scan-event parsing and uploaded Nmap XML parsing, then connect the resulting `parsed_signals` to the V2 recommendation engine without adding execution, subprocess calls, or external tool launches.
