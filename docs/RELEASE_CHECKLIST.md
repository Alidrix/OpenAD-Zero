# Release Checklist

## Code quality

- [ ] Backend tests pass
- [ ] Frontend build passes
- [ ] E2E tests pass
- [ ] Smoke tests pass

## Database

- [ ] Alembic migration created if models changed
- [ ] Migration reviewed manually
- [ ] Migration applied locally
- [ ] Downgrade reviewed if applicable

## Docker

- [ ] docker compose up --build works
- [ ] healthchecks pass
- [ ] worker starts
- [ ] optional BloodHound profile documented

## Product

- [ ] Capabilities updated
- [ ] README updated
- [ ] QA guide updated
- [ ] Demo seed works

## Security

- [ ] No secrets committed
- [ ] .env.example updated
- [ ] No arbitrary shell command added
- [ ] Uploaded files are not executed
