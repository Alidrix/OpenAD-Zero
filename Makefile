COMPOSE ?= docker compose
.PHONY: up up-build up-bloodhound down restart logs logs-api logs-worker logs-ui ps migrate migrate-local migration-new db-reset-dev seed-dev smoke test backend-install backend-test backend-lint backend-format backend-format-check frontend-install frontend-build frontend-e2e e2e lint format format-check security-check release-docs-check release-check version docker-security-check qa health clean

up:
	$(COMPOSE) up
up-build:
	$(COMPOSE) up --build
up-bloodhound:
	$(COMPOSE) --profile bloodhound up --build
down:
	$(COMPOSE) down
restart: down up
logs:
	$(COMPOSE) logs -f
logs-api:
	$(COMPOSE) logs -f openadzero-api
logs-worker:
	$(COMPOSE) logs -f openadzero-worker
logs-ui:
	$(COMPOSE) logs -f openadzero-ui
ps:
	$(COMPOSE) ps
migrate:
	$(COMPOSE) exec openadzero-api bash -lc "cd /app && alembic upgrade head"
migrate-local:
	./scripts/migrate.sh
migration-new:
	./scripts/migration-new.sh "$(MSG)"
db-reset-dev:
	./scripts/db-reset-dev.sh
seed-dev:
	./scripts/seed-dev.sh
smoke:
	./scripts/smoke.sh
test: backend-test frontend-build
backend-install:
	cd backend && python -m pip install -e ".[test]"
backend-test:
	cd backend && pytest
backend-lint:
	cd backend && ruff check app tests
backend-format:
	cd backend && ruff format app tests
backend-format-check:
	cd backend && ruff format --check app tests
frontend-install:
	cd frontend && npm ci
frontend-build:
	cd frontend && npm run build
frontend-e2e:
	cd frontend && npm run test:e2e
e2e: frontend-e2e
lint: backend-lint
format:
	make backend-format
format-check:
	make backend-format-check
security-check:
	./scripts/security-check.sh
release-docs-check:
	cd backend && pytest tests/test_release_docs.py
release-check:
	./scripts/release-check.sh
	make release-docs-check
version:
	@cat VERSION
docker-security-check:
	$(COMPOSE) run --rm openadzero-api id
	$(COMPOSE) run --rm openadzero-worker id
qa:
	make backend-lint
	make backend-test
	make frontend-build
	make security-check
	make smoke
	make e2e
health:
	curl -f http://localhost:8000/api/health
clean:
	$(COMPOSE) down -v
