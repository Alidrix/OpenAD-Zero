# Known Issues

## v0.1.0-rc1

### BloodHound CE optional configuration

BloodHound CE requires external configuration and is not required for standard OpenAD Zero startup.

### No PDF export

Only Markdown and HTML reporting are included in this release candidate.

### No multi-user authentication

This release candidate is designed for local or controlled use.

### E2E prerequisites

E2E tests require the frontend and API stack to be reachable.

### Tool availability

Nmap, NetExec and Nuclei availability depends on the backend Docker image or local environment.

### Release candidate status

This is not a stable v1.0 release. It is intended for controlled validation.

## Tailwind CSS v4 migration

OpenAD Zero v0.1.0-rc1 intentionally stays on Tailwind CSS v3.4.17.

Tailwind CSS v4 changes the PostCSS integration and requires a dedicated migration. This migration is deferred to v0.2.0 to keep the release candidate stable.
