# V2 Normalization Pipeline

Prompt 12 adds a parsing-only normalization layer for persisted evidence artifacts. The goal is to convert heterogeneous Windows/AD outputs into common V2 tables used by the orchestrator, GUI, approvals, and reporting without launching tools, creating RQ jobs, or invoking subprocesses.

## Normalized models

The existing asset/service/finding/signal/diagnostic tables remain the base schema. Prompt 12 adds AD graph and credential-risk models: `ParsedADObject`, `ParsedADRelation`, `ParsedAttackPath`, and `ParsedCredentialRisk`.

## Supported formats

- Nmap XML creates assets, services, service signals, domain-controller candidates, and diagnostics.
- Nuclei JSONL creates public findings, exposure signals, and line-level diagnostics. Raw request/response fields are omitted from public finding descriptions.
- NetExec SMB logs create SMB signals, findings, and credential-risk review rows.
- BloodHound/SharpHound ZIPs are parsed locally from JSON members. The parser rejects path traversal names and never extracts ZIP contents to arbitrary paths.
- LDAP, Kerberos, and ADCS normalizers accept future parsed JSON formats and return `parser_not_implemented` diagnostics for unsupported text.

## Idempotence

Normalizers use stable keys such as scan/IP, scan/IP/protocol/port, scan/template/source, scan/object ID, scan/relation endpoints, and credential-risk evidence hashes. Re-running normalization updates rows when possible instead of duplicating rows.

## Diagnostics and safety

Malformed XML, JSONL, ZIP, and unsupported formats create `ParseDiagnostic` rows. ZIP parsing reads members in memory after validating member names; it does not call `extract` or `extractall` and does not contact BloodHound or SharpHound.

## Orchestrator and reporting

The pentest orchestrator now loads normalized AD objects, relations, attack paths, and credential risks. These facts enrich metrics and can drive AD path analysis, credential-exposure review, and reporting recommendations.
