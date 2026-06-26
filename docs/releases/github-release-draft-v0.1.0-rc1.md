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
