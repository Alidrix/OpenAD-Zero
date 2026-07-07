# Prod-like deployment

OpenAD-Zero is intended for controlled lab and authorized pentest environments. It is not a multi-tenant SaaS platform.

Use `OPENADZERO_ENV=prod-like`, enable authentication, and provide a strong `OPENADZERO_API_TOKEN` via a secret file such as `/run/secrets/openadzero_api_token`. The startup checks reject empty values and weak placeholders such as `change-me`, `openadzero`, `password`, and `admin` in prod-like mode.

Recommended variables:

```env
OPENADZERO_ENV=prod-like
OPENADZERO_AUTH_ENABLED=true
OPENADZERO_API_TOKEN_FILE=/run/secrets/openadzero_api_token
POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
BLOODHOUND_API_TOKEN_FILE=/run/secrets/bloodhound_api_token
NEO4J_PASSWORD_FILE=/run/secrets/neo4j_password
OPENADZERO_AUTO_MIGRATE=false
OPENADZERO_REQUIRE_SCHEMA_READY=true
```

Expose the API only behind a trusted reverse proxy with TLS. Keep BloodHound/Neo4j behind the `bloodhound` Compose profile unless explicitly needed. Run `make migrate`, `make smoke`, and `./scripts/release-check.sh` before QA or release.
