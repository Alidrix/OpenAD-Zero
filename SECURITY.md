# Security Policy

Use GitHub private vulnerability reporting for coordinated disclosure. Do not publish exploit details before maintainers triage the issue.

## Tool execution model

OpenAD-Zero now distinguishes documented tools from runnable tools with the `executable_after_human_approval` integration status. Advanced AD/Pentest workflows such as Kerbrute, gMSADumper, DonPAPI, Coercer, BloodyAD, controlled Impacket workflows and Responder analyze mode are usable only through declared templates and explicit operator gates.

An OpenAD-Zero tool is executable only when:
1. the tool is declared in `tools.yml`;
2. the selected template is declared in `command_templates.py`;
3. the selected template is referenced by the tool;
4. the target is inside the validated scope;
5. the command preview has been generated;
6. human approval is confirmed;
7. explicit terms are accepted.

The frontend never sends a raw command to execute. The backend always rebuilds argv from an allowlisted template, refuses out-of-scope targets, refuses `0.0.0.0/0` and `::/0`, refuses public IPs by default, and keeps `manual_only`, `blocked_auto` and `planned` tools non-runnable. The GUI provides a dedicated landscape console per tool, separated terminal output and history, and a collapsible left sidebar grouped by Scope & Setup, Recon, SMB / NetExec, Active Directory, Coercion / Capture, Impacket, Credentials Review, Reports and Settings.

## Tool automation safeguards

Tool execution is template-only: raw commands are rejected, `shell=True` is not used, scope is revalidated at preview/approval/run time, public targets and broad default routes are refused, and preview hashes must match before execution. Secrets are redacted before API return and persisted findings use redacted evidence fingerprints for stable non-duplicated IDs. Metasploit controlled exploit requires an allowlisted enabled module, allowlisted options/payloads, successful prior check when required, and final human confirmation.
