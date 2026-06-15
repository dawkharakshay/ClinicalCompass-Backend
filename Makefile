.DEFAULT_GOAL := help

APP      := app.main:app
HOST     ?= 127.0.0.1
PORT     ?= 8000
DB_FILE  := clinicalcompass.db

COMPOSE  := docker compose

.PHONY: help install dev run lint format check test clean \
        up down build logs ps restart psql \
        seed_admin seed_admin_docker deploy_auth_guides

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install/sync dependencies from the lockfile
	uv sync

dev: ## Run the API with auto-reload
	uv run uvicorn $(APP) --reload --host $(HOST) --port $(PORT)

run: ## Run the API (no reload)
	uv run uvicorn $(APP) --host $(HOST) --port $(PORT)

lint: ## Lint with ruff
	uvx ruff check app

format: ## Auto-format with ruff
	uvx ruff format app
	uvx ruff check --fix app

check: ## Verify the app imports cleanly
	uv run python -c "from app.main import app; print('import OK')"

test: ## Run the test suite (requires pytest)
	uv run pytest -q

clean: ## Remove the SQLite DB and Python caches
	rm -f $(DB_FILE)
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +

generate_openapi: ## Generate OpenAPI schema to openapi.json
	uv run python -m utils.generate_openapi

# --- Docker Compose (Postgres + API + nginx) -------------------------------

up: ## Build and start the full stack in the background
	$(COMPOSE) up -d --build

down: ## Stop and remove the stack (keeps the DB volume)
	$(COMPOSE) down

build: ## Rebuild the API image
	$(COMPOSE) build

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

ps: ## Show the status of compose services
	$(COMPOSE) ps

restart: ## Restart the API service only
	$(COMPOSE) restart api

psql: ## Open a psql shell in the db container
	$(COMPOSE) exec db psql -U $${POSTGRES_USER:-clinicalcompass} -d $${POSTGRES_DB:-clinicalcompass}

seed_admin: ## Create/update the bootstrap admin user (local, from .env)
	uv run python -m utils.seed_admin

seed_admin_docker: ## Create/update the bootstrap admin user inside the api container
	$(COMPOSE) exec api uv run python -m utils.seed_admin

deploy_auth_guides: ## Add JSONB columns, rebuild API, reseed + verify auth guides (Docker)
	bash scripts/deploy_auth_guides.sh