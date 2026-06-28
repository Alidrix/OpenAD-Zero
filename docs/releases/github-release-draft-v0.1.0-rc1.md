# OpenAD Zero v0.1.0-rc1

OpenAD Zero v0.1.0-rc1 is the first release candidate of a safe-by-default Active Directory lab operations platform.

## Highlights

- Mission creation and internal scope validation.
- Nmap discovery.
- NetExec SMB safe enumeration.
- Nuclei safe web exposure scanning.
- BloodHound / SharpHound ZIP upload.
- BloodHound Explorer V1.
- Evidence Manager.
- Markdown/HTML Reporting Engine.
- Lab Operations Center.
- Timeline and Progress Score.
- RQ worker and persistent events.
- Docker Compose stack.
- CI, security checks and release checks.

## Safety model

This release intentionally excludes:

- automatic exploitation;
- credential dumping;
- LSASS dump;
- DCSync;
- pass-the-hash;
- persistence;
- EDR bypass;
- lateral movement automation;
- arbitrary shell command execution from the frontend.

## Install

```bash
cp .env.example .env
make up-build
make migrate
make smoke
```

## Validation

```bash
make backend-test
make frontend-build
make security-check
make release-check
```

## Notes

This is a release candidate intended for controlled, authorized environments such as internal labs, CTFs, training and safe assessment workflows.

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
