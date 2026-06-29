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


## Evidence storage

Tool automation persists run records, parsed findings, and generated artifacts under `EVIDENCE_DIR`. In Docker, `EVIDENCE_DIR` defaults to `/app/evidence`; the API and worker entrypoint creates `/app/evidence`, `/app/evidence/tool-runs`, `/app/evidence/findings`, and `/app/evidence/artifacts` before the application starts.

The entrypoint corrects permissions for Docker volumes when it starts as root and then drops to the application user `10001:10001`, so operators normally do not need to run manual `chown` or `chmod` commands. The recommended local Compose configuration uses the named volume `openadzero-evidence` to avoid host bind-mount permission problems. If you choose a bind mount such as `./evidence:/app/evidence` to export artifacts, host filesystem permissions can still vary by OS and may need to be managed outside the container.

## Local controlled execution model

`/api/tool-automation/preview`, `/approve`, and `/run` rebuild commands from backend allowlisted argv templates only. The frontend must not send raw commands. Preview returns a masked command and a SHA-256 hash computed over the canonical real argv. Run reconstructs the argv, revalidates scope, checks policy gates, compares the preview hash, executes with `subprocess.run(..., shell=False, timeout=300)`, redacts stdout/stderr, invokes parsers, and stores run/findings JSON under `EVIDENCE_DIR/tool-runs/` and `EVIDENCE_DIR/findings/`.

`GET /api/tool-automation/tool-health` reports installed/missing binaries. Metasploit controlled exploit is gated by `backend/app/tool_automation/metasploit_allowlist.yml`; disabled modules, unknown options, missing payload allowlist entries, missing successful checks, and missing final confirmation are refused. No exploit-all or arbitrary msfconsole strings are supported.

Local validation checklist:

- UI accessible on `localhost:5173`.
- API accessible on `localhost:8000`.
- Tool health reports available and missing binaries.
- Preview succeeds only for private in-scope targets and masks secrets.
- Run executes only the previewed command hash and stores redacted stdout/stderr/findings.
- Findings are parsed and secrets remain masked.

## Runtime writable directories

OpenAD-Zero keeps application code under `/app` and treats it as read-only at runtime. Do not make the full `/app` tree writable and do not run the final API or worker process as root.

Runtime output is split into two writable Docker volumes:

- `/app/evidence` stores durable evidence, tool run records, findings, and exported artifacts.
- `/app/runtime` stores external-tool runtime state: `HOME` in `/app/runtime/home`, XDG config in `/app/runtime/config`, cache in `/app/runtime/cache`, data in `/app/runtime/data`, temporary files in `/app/runtime/tmp`, and tool-specific state such as NetExec under `/app/runtime/home/.nxc`.

The Docker entrypoint creates these directories automatically, fixes ownership only for `/app/evidence` and `/app/runtime`, and then drops privileges to the `openadzero` user. Tool execution and tool-health checks pass `HOME`, `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME`, `TMPDIR`, and `NXC_PATH` values pointing at `/app/runtime`, so tools such as NetExec and Nuclei no longer try to write to `/app/.nxc` or `/app/.config`.

Operators should not run manual `chown -R` commands on `/app`, `/go`, `/opt/pipx`, `/usr/local`, or the container filesystem. Use `make check-permissions` to verify the API and worker can write to the expected runtime directories.
