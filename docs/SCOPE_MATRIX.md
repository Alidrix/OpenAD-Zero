# Scope Matrix

## Included in v0.1.0-rc1

| Area | Included |
| --- | --- |
| Mission creation | Yes |
| Internal scope validation | Yes |
| Nmap discovery | Yes |
| NetExec SMB safe enum | Yes |
| Nuclei safe web scan | Yes |
| BloodHound ZIP upload | Yes |
| BloodHound Explorer V1 | Yes |
| Evidence Manager | Yes |
| Markdown/HTML reporting | Yes |
| Lab Operations | Yes |
| Timeline | Yes |
| Progress Score | Yes |
| Docker Compose | Yes |
| RQ worker | Yes |
| CI | Yes |
| Security checks | Yes |
| Automatic exploitation | Yes |
| Credential dumping | Yes |
| LSASS dump | Yes |
| DCSync | Yes |
| Pass-the-hash | Yes |
| Persistence | Yes |
| EDR bypass | Yes |
| Lateral movement automation | Yes |
| Arbitrary shell command from frontend | Yes |
| PDF export | Yes |
| Multi-user auth | Yes |

## Tool automation safety gate

Human approval is a safety gate for approved read-only templates. Manual-only and blocked automation categories are not executed by OpenAD Zero, even after approval.

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
