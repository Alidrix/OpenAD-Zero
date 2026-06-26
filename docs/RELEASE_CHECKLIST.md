# Release Checklist

## Code quality

- [ ] `make backend-lint` passes.
- [ ] `make backend-format-check` passes.
- [ ] `make backend-test` passes.
- [ ] `make frontend-build` passes.
- [ ] `make e2e` passes.
- [ ] `make smoke` passes.
- [ ] `make release-check` passes.

## Security

- [ ] Dependency review passes.
- [ ] `make security-check` passes.
- [ ] Backend Docker containers run as non-root.
- [ ] Frontend dependencies are installed with `npm ci` from `package-lock.json`.
- [ ] No secrets committed.
- [ ] No arbitrary shell command added.
- [ ] Evidence paths remain under `EVIDENCE_DIR`.
- [ ] Uploaded files are not executed.

## Documentation

- [ ] `VERSION` contains `0.1.0-rc1`.
- [ ] `CHANGELOG.md` is complete.
- [ ] `docs/releases/v0.1.0-rc1.md` is complete.
- [ ] `docs/DEMO.md` is reviewed.
- [ ] README quick start and safety model are current.
- [ ] Capabilities metadata is current.

## Tag release

- [ ] Confirm current branch is clean after commit.
- [ ] Create annotated tag: `git tag -a v0.1.0-rc1 -m "OpenAD Zero v0.1.0-rc1"`.
- [ ] Push branch and tag: `git push && git push origin v0.1.0-rc1`.
- [ ] Publish GitHub release using `docs/releases/v0.1.0-rc1.md`.
