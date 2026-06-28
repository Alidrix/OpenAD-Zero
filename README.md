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
