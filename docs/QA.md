# QA

## Backend tests

```bash
cd backend
pytest
```

### Evidence directory

OpenAD Zero stores generated evidence under `EVIDENCE_DIR`.

- Docker default: `/app/evidence`
- Local/CI default: `./evidence`
- CI should set `EVIDENCE_DIR` to a writable temporary directory.

The backend refuses path traversal and creates evidence directories through a centralized path helper.
