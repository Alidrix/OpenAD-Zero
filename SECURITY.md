# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.1.0-rc1 | Yes |

## Reporting a vulnerability

Please do not open a public issue for security vulnerabilities.

Use GitHub private vulnerability reporting if enabled on this repository.

If private vulnerability reporting is not available, contact the maintainer privately and include:

- affected version;
- affected component;
- reproduction steps;
- expected impact;
- logs or screenshots if useful;
- whether the vulnerability affects confidentiality, integrity or availability.

## Scope

OpenAD Zero is a safe-by-default Active Directory lab operations platform.

Security reports are in scope when they affect:

- backend API security;
- evidence storage boundaries;
- path traversal protections;
- uploaded evidence handling;
- secret leakage;
- Docker runtime security;
- CI/CD security;
- frontend exposure of backend secrets;
- dependency vulnerabilities.

## Out of scope

The following are out of scope for this repository:

- requests to add exploitation automation;
- requests to add credential dumping;
- requests to add LSASS dump;
- requests to add DCSync;
- requests to add pass-the-hash;
- requests to add persistence;
- requests to add EDR bypass;
- reports based only on use against unauthorized targets.

## Safe handling

Uploaded evidence is never executed.

The frontend must never expose backend secrets such as:

- DATABASE_URL;
- REDIS_URL;
- BLOODHOUND_API_TOKEN;
- authorization headers;
- cookies.

Evidence paths must remain constrained under EVIDENCE_DIR.

## Response expectations

This is a community / release-candidate project.

The maintainer will try to acknowledge valid reports and prioritize fixes based on severity, exploitability and impact.
