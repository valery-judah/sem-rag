.DEFAULT_GOAL := help

DOCKER_COMPOSE ?= docker compose

.PHONY: help
help: ## Show this help message
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

.PHONY: sync
sync: ## Sync dependencies using uv
	uv sync

.PHONY: sync-llm
sync-llm: ## Sync optional model-backed embedding dependencies
	uv sync --group llm

.PHONY: sync-mac
sync-mac: ## Sync optional embedding and Apple Silicon generation dependencies
	uv sync --group llm --group mac

.PHONY: install
install: sync ## Install the package in editable mode
	uv pip install --editable .

.PHONY: fmt
fmt: ## Format and auto-fix lint issues
	uv run ruff format .
	uv run ruff check . --fix

.PHONY: fmt-check
fmt-check: ## Check formatting without modifying files
	uv run ruff format . --check

.PHONY: lint
lint: ## Run lint checks
	uv run ruff check .

.PHONY: type
type: ## Run static type checks
	uv run mypy src

.PHONY: test
test: install ## Run unit tests
	uv run pytest tests

.PHONY: test-e2e
test-e2e: install ## Run docker-backed end-to-end tests
	uv run pytest tests/e2e -m e2e -o addopts="-q -s"

.PHONY: smoke-llm
smoke-llm: ## Verify the optional embedding dependency group is installed
	uv run python -c "from doc_forge.indexing import require_sentence_transformers; require_sentence_transformers(); print('smoke-llm-ok')"

.PHONY: smoke-mac
smoke-mac: ## Verify the optional Apple Silicon generation dependency group is installed
	uv run python -c "from doc_forge.indexing import require_sentence_transformers; from doc_forge.query.answer_generation import require_mlx_lm; require_sentence_transformers(); require_mlx_lm(); print('smoke-mac-ok')"

.PHONY: verify
verify: fmt-check lint type test ## Run the read-only verification suite

.PHONY: check
check: verify ## Alias for the read-only verification suite

.PHONY: secret-scan
secret-scan: ## Scan tracked repository files for leaked Gemini API keys
	uv run python -m doc_forge.devtools.secret_scan --scope repo

.PHONY: secret-scan-staged
secret-scan-staged: ## Scan staged added lines for leaked Gemini API keys
	uv run python -m doc_forge.devtools.secret_scan --scope staged-added

.PHONY: install-git-hooks
install-git-hooks: ## Configure git to use repo-managed hooks
	git config core.hooksPath .githooks

.PHONY: run-api
run-api: install ## Run the internal lifecycle FastAPI app
	uv run uvicorn doc_forge.app.api:app --reload

.PHONY: run-worker
run-worker: install ## Run the internal lifecycle worker loop
	uv run python -m doc_forge.lifecycle.worker

.PHONY: migrate
migrate: install ## Apply Alembic migrations using DATABASE_URL
	@if [ -z "$(DATABASE_URL)" ]; then echo "DATABASE_URL is required"; exit 1; fi
	uv run alembic -c alembic.ini upgrade head

.PHONY: db-revision
db-revision: install ## Create a new Alembic revision with MESSAGE="..."
	@if [ -z "$(MESSAGE)" ]; then echo "MESSAGE is required"; exit 1; fi
	uv run alembic -c alembic.ini revision -m "$(MESSAGE)"

.PHONY: docker-build
docker-build: ## Build the local Docker image for the split runtime
	$(DOCKER_COMPOSE) build

.PHONY: docker-up
docker-up: ## Start the local Docker stack in detached mode
	$(DOCKER_COMPOSE) up -d

.PHONY: docker-up-build
docker-up-build: ## Build and start the local Docker stack in detached mode
	$(DOCKER_COMPOSE) up -d --build

.PHONY: docker-down
docker-down: ## Stop the local Docker stack
	$(DOCKER_COMPOSE) down

.PHONY: docker-ps
docker-ps: ## Show Docker stack service status
	$(DOCKER_COMPOSE) ps

.PHONY: docker-logs
docker-logs: ## Show recent API logs from the Docker stack
	$(DOCKER_COMPOSE) logs --tail=120 api

.PHONY: docker-db-shell
docker-db-shell: ## Open a psql shell inside the Docker Postgres service
	$(DOCKER_COMPOSE) exec db psql -U "$${POSTGRES_USER:-doc-forge}" -d "$${POSTGRES_DB:-doc-forge}"

.PHONY: docker-smoke
docker-smoke: ## Build, start, and probe the Docker stack readiness path
	$(DOCKER_COMPOSE) up -d --build
	@api_cid="$$( $(DOCKER_COMPOSE) ps -q api )"; \
	if [ -z "$$api_cid" ]; then \
		echo "api container not found"; \
		exit 1; \
	fi; \
	for attempt in $$(seq 1 30); do \
		status="$$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$$api_cid")"; \
		if [ "$$status" = "healthy" ]; then \
			break; \
		fi; \
		if [ "$$status" = "exited" ] || [ "$$status" = "dead" ]; then \
			echo "api container entered $$status state"; \
			$(DOCKER_COMPOSE) logs --tail=120 api; \
			exit 1; \
		fi; \
		sleep 2; \
	done; \
	status="$$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$$api_cid")"; \
	if [ "$$status" != "healthy" ]; then \
		echo "api container did not become healthy"; \
		$(DOCKER_COMPOSE) ps; \
		$(DOCKER_COMPOSE) logs --tail=120 api; \
		exit 1; \
	fi
	$(DOCKER_COMPOSE) exec -T api python -c "import os, urllib.request; print(urllib.request.urlopen(f\"http://127.0.0.1:{os.environ.get('PORT', '8000')}/readyz\", timeout=2).read().decode())"
