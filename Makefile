# AxiomQ developer commands. Run `make help` for the list.
SHELL := /bin/bash
COMPOSE := docker compose -f infra/compose/docker-compose.yml
UV := uv run
PY_TESTS := backend/tests quant_engine/tests workers/tests

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------- setup
.PHONY: install
install: ## Install Python (uv) and Node (pnpm) dependencies
	uv sync
	cd frontend && pnpm install --frozen-lockfile
	cd tests/e2e && pnpm install --frozen-lockfile

# ---------------------------------------------------------------- run
.PHONY: dev
dev: ## Run the full stack in Docker (web :3000, api :8000, mailpit :8025)
	$(COMPOSE) up --build

.PHONY: services
services: ## Start only PostgreSQL, Redis and Mailpit in Docker (for running apps locally)
	$(COMPOSE) up -d postgres redis mailpit

.PHONY: api
api: ## Run the API locally with reload (needs `make services` + `make migrate`)
	cd backend && $(UV) uvicorn axiomq_api.asgi:app --reload --port 8000

.PHONY: worker
worker: ## Run a worker locally
	$(UV) dramatiq axiomq_workers.main --processes 1 --threads 2

.PHONY: web
web: ## Run the frontend locally (proxies /api to AXIOMQ_API_URL, default :8000)
	cd frontend && pnpm dev

.PHONY: down
down: ## Stop the Docker stack
	$(COMPOSE) down

# ---------------------------------------------------------------- database
.PHONY: migrate
migrate: ## Apply database migrations
	cd backend && $(UV) alembic upgrade head

.PHONY: migration
migration: ## Create a migration: make migration m="describe change"
	cd backend && $(UV) alembic revision --autogenerate -m "$(m)"

.PHONY: seed
seed: ## Load development seed data (refuses to run in production)
	$(UV) python -m axiomq_api.cli seed

# ---------------------------------------------------------------- quality
.PHONY: lint
lint: ## Lint + format check + typecheck + architecture contracts (Python and TypeScript)
	$(UV) ruff check .
	$(UV) ruff format --check .
	$(UV) mypy backend/src quant_engine/src workers/src
	$(UV) lint-imports
	cd frontend && pnpm lint && pnpm typecheck && pnpm format:check

.PHONY: format
format: ## Auto-format Python and TypeScript
	$(UV) ruff check --fix .
	$(UV) ruff format .
	cd frontend && pnpm format

.PHONY: test
test: test-python ## Run Python unit + integration tests (needs PostgreSQL and Redis)

.PHONY: test-unit
test-unit: ## Run fast unit tests only (no database)
	$(UV) pytest -m "not integration" $(PY_TESTS)

.PHONY: test-python
test-python:
	$(UV) pytest $(PY_TESTS)

.PHONY: test-e2e
test-e2e: ## Build the frontend and run Playwright end-to-end tests
	cd frontend && pnpm build
	cd tests/e2e && pnpm exec playwright test

.PHONY: api-client
api-client: ## Regenerate the typed frontend API client from the backend OpenAPI schema
	./scripts/gen-api-client.sh

.PHONY: api-client-check
api-client-check: api-client ## Fail if the committed API client is out of date
	git diff --exit-code -- frontend/src/lib/api/schema.d.ts

# ---------------------------------------------------------------- build
.PHONY: build
build: ## Build production images
	docker build -f infra/docker/python.Dockerfile --target runtime -t axiomq-python:local .
	docker build -f infra/docker/frontend.Dockerfile --target runtime -t axiomq-web:local .
