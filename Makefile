.DEFAULT_GOAL := help

.PHONY: ensure-uv
ensure-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "Error: 'uv' is not installed or not on PATH."; \
		echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 127; \
	}

.PHONY: help
help: ## Show this help message
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

.PHONY: sync
sync: ensure-uv ## Sync dependencies using uv
	uv sync

.PHONY: init
init: sync install ## Bootstrap local dev environment

.PHONY: install
install: sync ## Install the package in editable mode
	uv pip install --editable .

.PHONY: add-rich
add-rich: ensure-uv ## Add `rich` dependency via uv (updates pyproject + uv.lock)
	uv add rich
	uv sync

.PHONY: fmt
fmt: ensure-uv ## Format and auto-fix lint issues
	uv run ruff format .
	uv run ruff check . --fix

.PHONY: lint
lint: ensure-uv ## Run lint checks
	uv run ruff format . --check
	uv run ruff check .

.PHONY: type
type: ensure-uv ## Run static type checks
	uv run mypy src

.PHONY: test
test: install ## Run unit tests
	uv run pytest tests

.PHONY: check
check: fmt lint type test ## Run all checks

.PHONY: run
run: install ## Run docforge demo CLI
	uv run python -m docforge.cli
