# Security notes

Do not commit `.env`, API tokens, database passwords, or BloodHound/Neo4j credentials. Do not put secrets in `VITE_*` variables because frontend build variables are public. Prefer `*_FILE` variables backed by `/run/secrets/*` or an external secret manager.

`/api/health` remains public for container healthchecks. Schema, DB, worker, tools, and application APIs require the API token when authentication is enabled. In `OPENADZERO_ENV=prod-like`, authentication is mandatory and weak default secrets are rejected at startup.
