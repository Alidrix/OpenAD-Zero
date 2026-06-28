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
