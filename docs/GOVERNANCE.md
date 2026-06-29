# OpenAD Zero Governance

## Project scope

OpenAD Zero is a safe-by-default Active Directory lab operations platform for authorized internal labs, CTFs, training environments and controlled assessment workflows.

## Release model

The project uses release candidate tags for early public milestones.

Current release candidate:

- v0.1.0-rc1

## Branch model

- main: stable development branch.
- feature branches: short-lived implementation branches.
- release tags: immutable release points.

## Pull request expectations

Every pull request should:

- describe the change;
- explain safety impact;
- pass CI;
- update tests when needed;
- update documentation when behavior changes;
- avoid adding arbitrary shell execution;
- avoid exposing secrets to the frontend.

## Security-sensitive changes

Changes in these areas require careful review:

- backend/app/core;
- backend/app/jobs;
- backend/app/api;
- backend/app/integrations;
- backend/app/evidence;
- backend/app/queue;
- backend/Dockerfile;
- docker-compose.yml;
- GitHub Actions workflows;
- scripts/security-check.sh.

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
