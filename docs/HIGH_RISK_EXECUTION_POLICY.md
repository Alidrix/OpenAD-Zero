# High-Risk Execution Policy

OpenAD-Zero treats Windows/AD offensive capabilities as deny-by-default. The controlled runner may execute only allowlisted, bounded, non-interactive templates after server-side approval, scope validation, command hashing, and parameter validation.

## Execution modes

- `safe_auto`: non-sensitive automation only.
- `approval_required`: bounded execution after standard approval.
- `reinforced_approval_required`: bounded execution after explicit reinforced approval.
- `preview_only`: information may be displayed or reviewed, but OpenAD-Zero does not execute it.
- `manual_only`: the operator may review the finding, but OpenAD-Zero intentionally will not run the action.
- `blocked`: the capability is forbidden by policy.

`preview_only`, `manual_only`, `blocked`, and `planned` templates must always have `supported_for_run=false`.

## Metasploit lock-down

Metasploit is sensitive. OpenAD-Zero allows only preview/read-only catalogue entries for search, info, metadata, and explicitly documented check previews. It does not launch `run`, `exploit`, `sessions`, payloads, listeners, Meterpreter, reverse/bind shells, post modules, upload/download, route changes, or interactive sessions. Free modules, free payloads, and free options are rejected by the central high-risk policy.

## Always blocked

Persistence, defense evasion, cleanup of traces, disabling security tooling, ransomware-like behavior, destructive actions, and exfiltration are `blocked`.

## Manual-only / blocked families

Credential dumping, LSASS/NTDS/SAM/DPAPI extraction, password spraying, brute force, credential stuffing, relay, coercion capture, command execution, lateral movement, AD write operations, exploitation, payloads, reverse/bind shells, and interactive sessions are `manual_only` or `blocked`.

## Approval and run rules

Approval preparation refuses `blocked`, `manual_only`, `preview_only`, and non-allowlisted high-risk templates. Run preparation repeats catalogue and high-risk checks before queueing and refuses non-runnable templates without consuming the approval or creating an RQ job.

## Decision examples

- SMB admin access detected → credential exposure review, not PsExec.
- Kerberoastable account detected → roastability review, not extraction or cracking.
- ADCS ESC candidate → ESC path analysis review, not exploitation.
- Dangerous ACL detected → AD path analysis, not DACL write.
- Metasploit → search/info/check preview-only, never run/exploit/payload/session.
