# V2 scope and parameter validation

Prompt 05 moves parameter safety into `backend/app/core/parameter_validation.py`. Validating only a top-level `target` is not enough because controlled templates can also receive `dc_ip`, `listener`, `source`, `rhost`, `url`, `artifact`, `userlist`, `wordlist`, `output`, credentials, enums and free text. Any of those can change the effective network destination or filesystem read/write location.

## Parameter types

Templates now declare explicit metadata:

- `scope_sensitive_params`: network destinations or sources validated against the authorized scope.
- `file_input_params`: existing files that must be under evidence or runtime roots.
- `file_output_params`: output paths sanitized and constrained to evidence/job directories.
- `credential_params`: passwords, hashes and tokens masked before previews/hashes are exposed.
- `free_text_params`: bounded text fields with control characters and shell metacharacters rejected.
- `enum_params`: strict allowlists for protocol, scheme, risk, execution mode, direction and similar values.

## Network validation

The backend performs static validation only. It supports IPv4 addresses, IPv4 CIDRs, hostnames/FQDNs only when a template explicitly allows them, and HTTP/HTTPS URLs only when a template explicitly allows URLs. Public IPs are refused unless `ALLOW_PUBLIC_SCANS` is enabled. `0.0.0.0/0`, `::/0`, IPv6, CIDRs broader than policy, dangerous URL schemes and shell separators are refused. No DNS resolution, ping, network contact or external tool execution is performed.

## File input validation

Input files such as `artifact`, `userlist`, `wordlist`, `input`, `input_file` and `targets_file` must resolve under `EVIDENCE_DIR` or `/app/runtime`. The validator refuses absolute paths outside those roots, `..` traversal, symlinks escaping the allowed roots, missing files and disallowed extensions when a template supplies an extension allowlist.

## File output validation

Output parameters such as `output`, `output_file`, `report_path` and `artifact_path` are sanitized and resolved under `EVIDENCE_DIR` or a controlled job directory. Writes to `/app/app`, `/usr`, `/etc`, `/root` or the source repository are rejected.

## Credentials, free text and enums

Credential parameters are never returned in cleartext by previews and are masked before approval hash payloads are built. NTLM hashes must match a 32-character hexadecimal format when declared as `ntlm_hash`. Free text has a maximum length, rejects null/control characters and shell metacharacters, and enums use strict allowlists.

## Enforcement points

- Preview: checks template id, rejects unexpected parameters, validates all metadata categories and returns masked credentials.
- Approval: rebuilds the server-side preview, validates inputs and scope before creating an approval, stores validated scope values in the scope snapshot and revalidates before approval.
- Future execution: the executor revalidates parameters and preview hashes instead of trusting preview results. RQ execution remains intentionally unconnected in this prompt.

This prompt adds no RQ jobs, no subprocess wiring, no exploit execution, no active DNS and no network probing.
