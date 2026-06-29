# OpenAD Zero

OpenAD Zero is a safe-by-default Active Directory lab operations platform for authorized internal labs, CTFs, training environments, and controlled assessment workflows.

It combines a FastAPI backend, React/Vite frontend, PostgreSQL, Redis, RQ worker, evidence handling, Markdown/HTML reporting, lab operations, timeline/progress views, and an explicit capability matrix.

## Quick start

```bash
cp .env.example .env
make up-build
make migrate
make smoke
```

Then open:

- UI: http://localhost:5173
- API: http://localhost:8000
- API health: http://localhost:8000/api/health
- Version: http://localhost:8000/api/version

SUPPORTED BY HTB - © 2026 Hack The Box

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

Release docs: docs/RELEASE_READINESS.md, docs/KNOWN_ISSUES.md, docs/POST_RELEASE.md.

### Controlled Metasploit exploitation

OpenAD-Zero can prepare and run controlled Metasploit exploit workflows only when the module is allowlisted, the target is in scope, the command is generated from a backend template, the preview is reviewed, the preview hash matches at execution time, a check step has been performed when required, human approval is confirmed, terms are accepted and final exploit confirmation is confirmed.

There is no free `msfconsole` command, no automatic exploitation, no implicit multi-target exploitation, no non-allowlisted payload, no automatic post-exploitation, no persistence, no log or trace deletion, no anti-forensics and no out-of-scope execution.
