COMPOSE ?= docker compose
.PHONY: up up-build up-bloodhound down restart logs logs-api logs-worker logs-ui ps migrate migrate-local migration-new db-reset-dev seed-dev seed-demo e2e e2e-ui e2e-report qa demo smoke test backend-test frontend-build lint format health clean
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
seed-demo:
	$(COMPOSE) exec openadzero-api python scripts/seed_demo.py
e2e:
	cd frontend && npm run test:e2e
e2e-ui:
	cd frontend && npm run test:e2e:ui
e2e-report:
	cd frontend && npm run test:e2e:report
qa:
	$(MAKE) backend-test
	$(MAKE) frontend-build
	$(MAKE) e2e
demo:
	$(MAKE) up-build
	$(MAKE) migrate
	$(MAKE) seed-demo
smoke:
	./scripts/smoke.sh
test: backend-test frontend-build
backend-test:
	cd backend && pytest
frontend-build:
	cd frontend && npm run build
lint:
	cd backend && python -m compileall app
format:
	@echo "No formatter configured."
health:
	curl -f http://localhost:8000/api/health
clean:
	$(COMPOSE) down -v
