# Release Checklist

## Code quality

- [ ] Backend lint passes
- [ ] Backend tests pass
- [ ] Frontend build passes
- [ ] E2E tests pass
- [ ] Smoke tests pass

## Security

- [ ] Dependency review passes
- [ ] No secrets committed
- [ ] No arbitrary shell command added
- [ ] Evidence paths remain under EVIDENCE_DIR
- [ ] Uploaded files are not executed

## Docker

- [ ] docker compose up --build works
- [ ] API healthcheck passes
- [ ] Worker healthcheck passes
- [ ] Redis healthcheck passes
- [ ] PostgreSQL healthcheck passes
- [ ] Optional BloodHound profile remains optional

## Documentation

- [ ] README updated
- [ ] docs/QA.md updated
- [ ] docs/DOCKER.md updated if Docker changed
- [ ] capabilities.yml updated if capabilities changed

## Release

- [ ] Version tag created
- [ ] Release notes written
