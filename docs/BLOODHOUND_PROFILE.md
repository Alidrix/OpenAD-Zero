# Optional BloodHound CE Docker profile

BloodHound CE is optional. OpenAD Zero does not depend on it by default.

## Enable

```bash
cp .env.example .env
make up-bloodhound
```

## Variables

- `BLOODHOUND_ENABLED`
- `BLOODHOUND_BASE_URL`
- `BLOODHOUND_API_TOKEN`
- `BLOODHOUND_VERIFY_TLS`
- `BLOODHOUND_POSTGRES_USER`
- `BLOODHOUND_POSTGRES_PASSWORD`
- `BLOODHOUND_POSTGRES_DB`
- `BLOODHOUND_NEO4J_AUTH`

Replace all `change-me-*` values before any shared or production-like deployment. Do not commit real tokens.

## Limits

The profile is for local integration convenience. It does not add a mandatory dependency and does not enable new offensive runners.
