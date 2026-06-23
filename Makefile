COMPOSE ?= docker compose
up:
	$(COMPOSE) up --build
down:
	$(COMPOSE) down
logs:
	$(COMPOSE) logs -f
test: backend-test frontend-build
backend-test:
	cd backend && pytest
frontend-build:
	cd frontend && npm install && npm run build
