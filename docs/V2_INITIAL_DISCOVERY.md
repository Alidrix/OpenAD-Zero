# V2 Initial Discovery

OpenAD-Zero V2 can start a safe initial network discovery from an existing scan with:

`POST /api/v2/scans/{scan_id}/start-initial-discovery`

The endpoint is protected by the existing API authentication dependency and only accepts:

```json
{"profile":"safe_default"}
```

Extra fields such as `command`, `argv`, `shell`, `raw_command`, `targets`, or free-form Nmap options are rejected by Pydantic `extra="forbid"`.

## Safe profile

`safe_default` is reconstructed server-side as:

```text
nmap -Pn -sV --top-ports 1000 -oX <EVIDENCE_DIR>/initial-discovery/<scan_id>/nmap.xml <validated_targets>
```

Allowed options are only `-Pn`, `-sV`, `--top-ports 1000`, `-oX` to the controlled XML path, and targets from validated mission scope.

Forbidden at this stage: `-A`, `--script`, `--script-args`, `-O`, `-sU`, `-p-`, `--min-rate`, spoofing/evasion options, raw frontend commands, and all high-risk tools.

## Artifacts

The worker stores `nmap.xml`, `stdout.log`, `stderr.log`, and `command.masked.txt` under `EVIDENCE_DIR/initial-discovery/<scan_id>/`. The scan artifact record points to the XML file only after validating that the path remains under `EVIDENCE_DIR`.

## Parsing and recompute

After Nmap completes, the existing V2 parsing service imports Nmap XML hosts as `ParsedAsset` rows, open ports as `ParsedService` rows, and service-derived signals such as `smb_detected`, `ldap_detected`, `kerberos_detected`, `http_detected`, `rdp_detected`, `winrm_detected`, and `mssql_detected`. Malformed XML produces `ParseDiagnostic` entries instead of crashing the API.

The worker then calls `PentestOrchestrator(db).recompute(scan_id)`. This only proposes next actions from normalized facts; it does not execute NetExec, Nuclei, Impacket, Kerbrute, Coercer, DonPAPI, Metasploit, Responder, or any exploit workflow.

## Events

The workflow persists progress events from `scan.initial_discovery_queued` through `scan.initial_discovery_completed` or `scan.initial_discovery_failed`. Payloads contain scan id, progress, current step, job/artifact identifiers when available, and sanitized errors only.

## Follow-on recommendations

After Nmap parsing, the pentest orchestrator recompute step applies Prompt 07 decision rules to SMB, LDAP/Kerberos, web, remote management, MSSQL, ADCS, BloodHound, credential exposure, and reporting signals.


## Prompt 12 normalization update

V2 artifact outputs now flow through `backend/app/normalization/` where supported Nmap, Nuclei, NetExec SMB, BloodHound ZIP, LDAP, Kerberos, and ADCS artifacts are converted into common parsed tables. This remains parsing-only: no extra tool launch, no new RQ job creation, and no subprocess is introduced by normalization.
