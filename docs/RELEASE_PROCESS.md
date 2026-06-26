# Release Process

## Pre-release checks

```bash
cp .env.example .env
make up-build
make migrate
make smoke
make backend-test
make frontend-build
make security-check
make release-check
```

## Verify version

```bash
cat VERSION
curl http://localhost:8000/api/version
```

Expected version:

```text
0.1.0-rc1
```

## Create Git tag

```bash
git status
git checkout main
git pull
git tag -a v0.1.0-rc1 -m "OpenAD Zero v0.1.0-rc1"
git push origin v0.1.0-rc1
```

## Create GitHub release

Use GitHub release UI or GitHub CLI:

```bash
gh release create v0.1.0-rc1 \
  --title "OpenAD Zero v0.1.0-rc1" \
  --notes-file docs/releases/v0.1.0-rc1.md \
  --prerelease
```

## Post-release

* Verify release page.
* Verify source archive.
* Verify README links.
* Create v0.1.0 milestone if needed.
* Create v0.2.0 milestone if needed.
