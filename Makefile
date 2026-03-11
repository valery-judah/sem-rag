.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

.PHONY: sync
sync: ## Sync dependencies using uv
	uv sync

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

.PHONY: verify
verify: fmt-check lint type test ## Run the read-only verification suite

.PHONY: check
check: verify ## Alias for the read-only verification suite

.PHONY: secret-scan
secret-scan: ## Scan tracked repository files for leaked Gemini API keys
	uv run python -m parity.devtools.secret_scan --scope repo

.PHONY: secret-scan-staged
secret-scan-staged: ## Scan staged added lines for leaked Gemini API keys
	uv run python -m parity.devtools.secret_scan --scope staged-added

.PHONY: install-git-hooks
install-git-hooks: ## Configure git to use repo-managed hooks
	git config core.hooksPath .githooks

.PHONY: run
run: install ## Run parity demo CLI
	uv run python -m parity.cli

.PHONY: run-api
run-api: install ## Run the internal lifecycle FastAPI app
	uv run uvicorn parity.app.api:app --reload

.PHONY: run-worker
run-worker: install ## Run the internal lifecycle worker loop
	uv run python -m parity.lifecycle.worker

.PHONY: migrate
migrate: install ## Apply Alembic migrations using DATABASE_URL
	@if [ -z "$(DATABASE_URL)" ]; then echo "DATABASE_URL is required"; exit 1; fi
	uv run alembic -c alembic.ini upgrade head

.PHONY: db-revision
db-revision: install ## Create a new Alembic revision with MESSAGE="..."
	@if [ -z "$(MESSAGE)" ]; then echo "MESSAGE is required"; exit 1; fi
	uv run alembic -c alembic.ini revision -m "$(MESSAGE)"
