## Summary

Describe the change.

## Type of change

- [ ] Bug fix
- [ ] Documentation
- [ ] Refactor
- [ ] Security hardening
- [ ] Test / CI
- [ ] Feature within existing safe scope

## Safety checklist

- [ ] No arbitrary shell command added
- [ ] No credential dumping
- [ ] No exploitation automation
- [ ] No secrets committed
- [ ] Evidence paths remain under EVIDENCE_DIR
- [ ] Frontend does not expose backend secrets

## Validation

- [ ] make backend-test
- [ ] make frontend-build
- [ ] make security-check
- [ ] make smoke
- [ ] make release-check

## Notes

Add anything reviewers should know.
