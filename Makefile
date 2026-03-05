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

.PHONY: lint
lint: ## Run lint checks
	uv run ruff format . --check
	uv run ruff check .

.PHONY: type
type: ## Run static type checks
	uv run mypy src

.PHONY: test
test: install ## Run unit tests
	uv run pytest tests

.PHONY: check
check: fmt lint type test ## Run all checks

.PHONY: secret-scan
secret-scan: ## Scan tracked repository files for leaked Gemini API keys
	uv run python -m docforge.devtools.secret_scan --scope repo

.PHONY: secret-scan-staged
secret-scan-staged: ## Scan staged added lines for leaked Gemini API keys
	uv run python -m docforge.devtools.secret_scan --scope staged-added

.PHONY: install-git-hooks
install-git-hooks: ## Configure git to use repo-managed hooks
	git config core.hooksPath .githooks

.PHONY: run
run: install ## Run docforge demo CLI
	uv run python -m docforge.cli
