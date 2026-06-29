# Tool Automation Library

OpenAD Zero separates documentation, preview, approval, and execution. Human approval is a safety gate for approved read-only templates.

Human approval is required for assisted safe actions, but human approval does not allow OpenAD Zero to execute blocked actions.

## Integration statuses

| Status | Meaning |
| --- | --- |
| `safe_auto` | Can be launched automatically when risk is low and scope is validated. |
| `assisted_safe` | Can be previewed and launched after human approval. Only read-only enumeration or audit templates are eligible. |
| `manual_only` | No backend execution. OpenAD Zero provides documentation, a manual action card, and external evidence import. |
| `blocked_auto` | No backend execution, no Run button, and no executable approval. Only limited documentation and a security warning are allowed. |
| `planned` | Not available. |

## Approved read-only templates

The only assisted-safe templates in this version are:

- Nmap safe discovery.
- NetExec SMB fingerprint.
- NetExec SMB signing check.
- NetExec SMB null session check.
- Nuclei safe templates.
- enum4linux-ng basic JSON/quick mode when installed.

Sensitive Impacket scripts, Responder poisoning/capture, coercion, credential dumping, LSASS access, DCSync, pass-the-hash, relay, DPAPI/SAM/LSA/NTDS dumping, AD modification, persistence, shell, and reverse-shell workflows are not executed by OpenAD Zero.

## Manual-only workflow

Manual-only tools show these actions:

- View details.
- Create manual note.
- Import evidence.

The manual-only user message is:

> Usage manuel uniquement. OpenAD Zero peut créer une carte d’action manuelle et importer les résultats comme evidence.

## Blocked automation policy

Blocked automation categories have no Run button, no active run endpoint, no executable command template, no approval that permits execution, no backend command, no RQ job, and no subprocess. Human approval cannot bypass this rule.

## Manual use outside OpenAD Zero

Some tools or techniques may be used manually by an authorized operator in a controlled engagement or lab.

OpenAD Zero may document that a manual action was performed and may import external evidence produced outside the platform.

However, OpenAD Zero does not execute blocked automation categories itself, even after human approval.

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

## Controlled Metasploit exploitation

OpenAD-Zero can prepare and run controlled Metasploit exploit workflows only when:

1. the module is allowlisted in `backend/app/tool_automation/metasploit_allowlist.yml`;
2. the target is in scope;
3. the command is generated from a backend template;
4. the command preview is reviewed;
5. the preview hash matches at execution time;
6. a check step has been performed when required;
7. human approval is confirmed;
8. terms are accepted;
9. final exploit confirmation is confirmed.

Prepared exploit does not mean executed exploit. An exploit command may be generated and previewed, but it must never run without explicit human approval, terms acceptance, valid scope and a matching preview hash.

Metasploit controlled exploitation forbids free `msfconsole` commands, automatic exploitation without human action, implicit multi-target exploitation, non-allowlisted payloads, automatic post-exploitation, persistence, log deletion, trace removal, anti-forensics and any execution outside validated scope. Correlation from Nmap, Nuclei, NetExec, SMB, LDAP, Kerberos and BloodHound may suggest a potential controlled exploit candidate, but the suggestion is never directly executable and always requires manual review, check, preview and final confirmation.
