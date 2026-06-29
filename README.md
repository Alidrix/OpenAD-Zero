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

## Evidence storage

Runs, findings, uploaded evidence, reports, and generated tool artifacts are stored under `EVIDENCE_DIR`. In Docker the default path is `/app/evidence`, with `tool-runs`, `findings`, and `artifacts` subdirectories created automatically for both the API and worker containers.

The Docker entrypoint initializes `/app/evidence`, fixes Docker volume permissions when the container starts as root, and then runs the application as the non-root `openadzero` user (`10001:10001`). You should not need to run manual `chown` or `chmod` commands for normal local startup.

The default Compose setup uses the named Docker volume `openadzero-evidence`, which is recommended because it avoids common Linux host bind-mount ownership issues. If you intentionally override the volume with a bind mount such as `./evidence:/app/evidence` to export artifacts to the working tree, Docker may still require host-specific permissions depending on your OS and filesystem.

## Local LAB startup

```bash
cp .env.example .env
make up-build
make migrate
make smoke
pytest
cd frontend && npm install && npm run build
```

Tool automation exposes `/api/tool-automation/tool-health` for binary status and stores local run history under `EVIDENCE_DIR/tool-runs/` plus findings under `EVIDENCE_DIR/findings/`.
