# Windows/AD Tool Catalog

OpenAD-Zero keeps Windows/Active Directory tooling in a central catalogue so recommendations, approvals, readiness, and future parsers share the same safety metadata. The catalogue is descriptive first: adding an entry does not make it executable.

## Families

Mandatory families are: `network_discovery`, `service_fingerprinting`, `smb_enumeration`, `ldap_ad_enumeration`, `kerberos_review`, `adcs_review`, `bloodhound_analysis`, `web_surface_review`, `vulnerability_analysis`, `credential_exposure_review`, `coercion_capture_review`, `remote_management_review`, `mssql_review`, `rdp_review`, `evidence_reporting`, and `manual_only_sensitive`.

Each family declares its pentest phase, default risk, supported tools, default execution mode, and safety notes.

## Execution modes and risk

- `safe_auto`: parsing/reporting/health checks and narrowly bounded read-only work only.
- `approval_required`: bounded read-only enumeration or safe template review.
- `reinforced_approval_required`: Kerberos user enumeration previews, credentialed checks, coercion/ADCS/Impacket-sensitive previews, or noisy authentication-adjacent workflows.
- `manual_only`: sensitive operator workflows such as dumping, spraying, brute force, lateral movement, persistence, and active capture.
- `blocked`: destructive, out-of-scope, raw payload, shell, cleanup, exfiltration, or ransomware-like behavior.

Risk levels are `info`, `low`, `medium`, `high`, and `critical`. High/critical templates are never `safe_auto`.

## Supported for run

Prompt 11 keeps the Prompt 10 executable perimeter only:

- `nmap_safe_discovery`
- `netexec_smb_fingerprint`
- `netexec_smb_signing_check`
- `netexec_smb_null_session_check`
- `netexec_smb_null_session_shares`
- `nuclei_safe_templates`
- `nuclei_web_exposure_scan`

All still require backend reconstruction, validated scope, approved action state, matching approval hash, and the existing RQ runner path.

## Preview-only and planned templates

LDAP/AD, Kerberos review, ADCS review, BloodHound analysis, Nuclei CVE/misconfiguration review, WinRM/RDP/WMI/MSSQL review, credential exposure reporting, Coercer/Responder analyze previews, and Impacket read-oriented previews are catalogued for future parser/normalization prompts. They are not executable unless a later prompt explicitly promotes them after safety review.

## Manual-only and blocked examples

`mimikatz`, `lsass_dump`, `secretsdump`, `pass_the_hash`, `password_spray`, `bruteforce`, `lateral_movement_execution`, `persistence`, and `trace_cleanup` are visible in the catalogue as non-executable sensitive workflows. OpenAD-Zero must never run them automatically.

## Readiness

`GET /api/v2/tool-catalog/readiness` checks `shutil.which()` for declared binaries and reports availability, missing reason, integration status, supported templates, guarded templates, and risk summary. It does not execute tool binaries, request versions, or contact the network.

## Approvals and RQ run

Approval preparation refuses manual-only/blocked templates. Run preparation accepts only `supported_for_run=true` templates that are approved, in scope, and hash-consistent. Preview-only/manual-only/blocked/planned templates return clean `501` or `403` style errors and do not consume approvals.

## Deliberately forbidden

No raw frontend command, `shell=True`, arbitrary NSE/template paths, remote Nuclei templates, SharpHound launch, coercion capture, relay, credential dumping, pass-the-hash, password spraying, brute force, command execution, persistence, trace cleanup, or exploit automation is enabled by this catalogue.


## Prompt 12 normalization update

V2 artifact outputs now flow through `backend/app/normalization/` where supported Nmap, Nuclei, NetExec SMB, BloodHound ZIP, LDAP, Kerberos, and ADCS artifacts are converted into common parsed tables. This remains parsing-only: no extra tool launch, no new RQ job creation, and no subprocess is introduced by normalization.
