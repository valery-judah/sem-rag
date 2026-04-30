.DEFAULT_GOAL := help

# Make is the single entry point for repository workflows. Python work calls
# Poe tasks in poe_tasks.toml; Docker work calls Docker Compose. Target names
# start with the part of the system they act on: setup-, app-, db-, stack-,
# observability-, query-context-, e2e-, docs-. Checks (fmt, lint, type, test,
# verify) keep short names. Pass extra arguments with ARGS='...'.

-include .env
export DATABASE_URL ?= postgresql+psycopg://doc-forge:doc-forge@localhost:5432/doc-forge
export DOC_FORGE_ARTIFACT_ROOT ?= ./data
export DOC_FORGE_ENVIRONMENT ?= dev
# Compose runs api and worker as this user so they can write to ./data.
export DOC_FORGE_UID ?= $(shell id -u)
export DOC_FORGE_GID ?= $(shell id -g)
# The observability Postgres, built from the defaults in docker-compose.observability.yml.
OBSERVABILITY_DATABASE_URL := $(or $(DOC_FORGE_OBSERVABILITY_DATABASE_URL),postgresql+psycopg://$(or $(OBSERVABILITY_POSTGRES_USER),doc_forge):$(or $(OBSERVABILITY_POSTGRES_PASSWORD),doc_forge)@localhost:$(or $(OBSERVABILITY_POSTGRES_PORT),5433)/$(or $(OBSERVABILITY_POSTGRES_DB),doc_forge_observability))

UV := uv
POE := $(UV) run poe
COMPOSE ?= docker compose
STACK_COMPOSE := $(COMPOSE) -f docker-compose.yml
OBSERVABILITY_COMPOSE := $(COMPOSE) -f docker-compose.observability.yml
ARGS ?=
MESSAGE ?=
QUERY_ID ?=
TYPE ?=
SLUG ?=

SETUP_TARGETS := setup setup-sync setup-llm setup-mac setup-lock setup-hooks clean-preview clean
CHECK_TARGETS := verify fmt fmt-check lint type test secret-scan secret-scan-staged
APP_TARGETS := app-api app-worker
DB_TARGETS := db-migrate db-revision db-shell
STACK_TARGETS := stack-up stack-up-db stack-build stack-status stack-logs stack-log-paths stack-down stack-clean
OBSERVABILITY_TARGETS := observability-up observability-status observability-logs observability-down observability-scan
QUERY_TARGETS := query-context-collect query-context-show
E2E_TARGETS := e2e-test e2e-ingest e2e-compare-backends
DOCS_TARGETS := docs-workstream-new
ALIAS_TARGETS := install-git-hooks workstream-new docker-build docker-up docker-up-build docker-down docker-clean docker-logs docker-log-index docker-db-shell observability-up-build

.PHONY: help
help: ## Show this help message
	@echo "Usage: make <target> [ARGS='<extra arguments>']"
	@echo ""
	@print_section() { \
		title="$$1"; \
		targets="$$2"; \
		echo "$$title:"; \
		for target in $$targets; do \
			awk -v target="$$target" 'BEGIN {FS = ":.*## "} $$0 ~ ("^" target ":.*## ") {printf "  %-24s %s\n", target, $$2; exit}' $(MAKEFILE_LIST); \
		done; \
		echo ""; \
	}; \
	print_section "Setup" "$(SETUP_TARGETS)"; \
	print_section "Checks (read-only except fmt)" "$(CHECK_TARGETS)"; \
	print_section "App on the host (foreground, needs make stack-up-db)" "$(APP_TARGETS)"; \
	print_section "Database" "$(DB_TARGETS)"; \
	print_section "Local Docker stack: db, api, worker" "$(STACK_TARGETS)"; \
	print_section "Observability stack: Postgres, Loki, Vector, Grafana" "$(OBSERVABILITY_TARGETS)"; \
	print_section "Query context bundles" "$(QUERY_TARGETS)"; \
	print_section "End-to-end checks (Docker)" "$(E2E_TARGETS)"; \
	print_section "Docs" "$(DOCS_TARGETS)"; \
	print_section "Aliases for old names (use the new names)" "$(ALIAS_TARGETS)"

.PHONY: ensure-uv
ensure-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "Error: 'uv' is not installed or not on PATH."; \
		echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 127; \
	}

# --- Setup ---

.PHONY: setup
setup: setup-sync setup-hooks ## Sync dependencies and configure Git hooks

.PHONY: setup-sync
setup-sync: ensure-uv ## Sync the default and dev dependencies into .venv (removes the llm and mac groups)
	$(UV) sync

.PHONY: setup-llm
setup-llm: ensure-uv ## Also install the llm group for sentence-transformers embeddings, then check it
	$(UV) sync --group llm
	$(POE) setup-check-llm

.PHONY: setup-mac
setup-mac: ensure-uv ## Also install the llm and mac groups for MLX generation on Apple Silicon, then check them
	$(UV) sync --group llm --group mac
	$(POE) setup-check-mac

.PHONY: setup-lock
setup-lock: ensure-uv ## Generate or refresh uv.lock (writes tracked files)
	$(UV) lock

.PHONY: setup-hooks
setup-hooks: ## Configure Git to use the hooks in .githooks/
	@if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then \
		git config core.hooksPath .githooks; \
	else \
		echo "Not in a git repository. Skipping git hooks setup."; \
	fi

.PHONY: clean-preview
clean-preview: ensure-uv ## List what clean would remove, without removing anything
	$(POE) clean --dry-run $(ARGS)

.PHONY: clean
clean: ensure-uv ## Remove generated local state and keep repository inputs (ARGS='--include-model-cache')
	$(POE) clean $(ARGS)

# --- Checks ---

.PHONY: verify
verify: ensure-uv ## Run format check, lint, types, and unit tests
	$(POE) verify

.PHONY: fmt
fmt: ensure-uv ## Format code and auto-fix lint issues (writes files)
	$(POE) fmt

.PHONY: fmt-check
fmt-check: ensure-uv ## Check formatting without changing files
	$(POE) fmt-check

.PHONY: lint
lint: ensure-uv ## Run lint checks
	$(POE) lint

.PHONY: type
type: ensure-uv ## Run strict type checks
	$(POE) type

.PHONY: test
test: ensure-uv ## Run unit tests (ARGS='-k <expr>' to filter)
	$(POE) test $(ARGS)

.PHONY: secret-scan
secret-scan: ensure-uv ## Scan tracked files for leaked keys
	$(POE) secret-scan

.PHONY: secret-scan-staged
secret-scan-staged: ensure-uv ## Scan staged added lines for leaked keys (used by the pre-commit hook)
	$(POE) secret-scan-staged

# --- App on the host ---

.PHONY: app-api
app-api: ensure-uv ## Run the API on http://127.0.0.1:8000 with reload (foreground)
	$(POE) app-api

.PHONY: app-worker
app-worker: ensure-uv ## Run the lifecycle worker loop (foreground)
	$(POE) app-worker

# --- Database ---

.PHONY: db-migrate
db-migrate: ensure-uv ## Apply Alembic migrations to DATABASE_URL
	$(POE) db-migrate

.PHONY: db-revision
db-revision: ensure-uv ## Create an Alembic revision (MESSAGE='<summary>', writes files)
	@test -n "$(MESSAGE)" || { echo "Usage: make db-revision MESSAGE='<summary>'"; exit 2; }
	$(POE) db-revision "$(MESSAGE)"

.PHONY: db-shell
db-shell: ## Open an interactive psql shell in the stack's Postgres (ARGS='-c "<sql>"' to run one query)
	$(STACK_COMPOSE) exec db psql -U "$${POSTGRES_USER:-doc-forge}" -d "$${POSTGRES_DB:-doc-forge}" $(ARGS)

# --- Local Docker stack ---

.PHONY: stack-up
stack-up: ensure-uv ## Build and start db, api, and worker in Docker; returns once they are healthy
	@eval "$$($(UV) run python -m doc_forge.devtools.docker_local_generator shell-env)"; \
	run_id="$$(./scripts/prepare_compose_logs.sh)"; \
	echo "compose log run id: $$run_id"; \
	DOC_FORGE_LOG_RUN_ID="$$run_id" $(STACK_COMPOSE) up --build --detach --wait
	@echo "API: http://127.0.0.1:$${PORT:-8000}"

.PHONY: stack-up-db
stack-up-db: ## Start only Postgres, for app-api and app-worker on the host; returns once it is healthy
	$(STACK_COMPOSE) up --detach --wait db

.PHONY: stack-build
stack-build: ## Build the stack images without starting them
	$(STACK_COMPOSE) build

.PHONY: stack-status
stack-status: ## Show the state of the stack containers
	$(STACK_COMPOSE) ps --all

.PHONY: stack-logs
stack-logs: ## Print recent stack logs (ARGS='api' for one service, ARGS='--follow' to keep following)
	$(STACK_COMPOSE) logs --tail=120 $(ARGS)

.PHONY: stack-log-paths
stack-log-paths: ## Print where archived Compose, e2e, and query context files are
	@echo "compose latest:"
	@printf "  %s\n" "$(CURDIR)/data/logs/compose/latest/api.jsonl"
	@printf "  %s\n" "$(CURDIR)/data/logs/compose/latest/worker.jsonl"
	@echo "e2e latest root:"
	@printf "  %s\n" "$(CURDIR)/data/logs/e2e/latest"
	@echo "query context root:"
	@printf "  %s\n" "$(CURDIR)/data/context/queries"

.PHONY: stack-down
stack-down: ## Stop and remove the stack containers; keeps the database volume
	$(STACK_COMPOSE) down

.PHONY: stack-clean
stack-clean: ## Stop the stack and delete its volumes, including the database (deletes data)
	$(STACK_COMPOSE) down -v

# --- Observability stack ---

.PHONY: observability-up
observability-up: ## Build and start the observability stack; returns once it runs
	$(OBSERVABILITY_COMPOSE) up --build --detach --wait
	@echo "Grafana: http://127.0.0.1:$${OBSERVABILITY_GRAFANA_PORT:-3000}"

.PHONY: observability-status
observability-status: ## Show the state of the observability containers
	$(OBSERVABILITY_COMPOSE) ps --all

.PHONY: observability-logs
observability-logs: ## Print recent observability logs (ARGS='<service>' or ARGS='--follow')
	$(OBSERVABILITY_COMPOSE) logs --tail=120 $(ARGS)

.PHONY: observability-down
observability-down: ## Stop and remove the observability containers; keeps their volumes
	$(OBSERVABILITY_COMPOSE) down

.PHONY: observability-scan
observability-scan: ensure-uv ## Index collected query bundles into the observability Postgres (needs observability-up)
	@DOC_FORGE_OBSERVABILITY_DATABASE_URL='$(OBSERVABILITY_DATABASE_URL)' $(POE) observability-scan

# --- Query context bundles ---

.PHONY: query-context-collect
query-context-collect: ensure-uv ## Collect one query's trace, replay, logs, and eval data (QUERY_ID=<id>)
	@test -n "$(QUERY_ID)" || { echo "Usage: make query-context-collect QUERY_ID=<id>"; exit 2; }
	$(POE) query-context-collect "$(QUERY_ID)"

.PHONY: query-context-show
query-context-show: ensure-uv ## Show the files of a collected query context bundle (QUERY_ID=<id>)
	@test -n "$(QUERY_ID)" || { echo "Usage: make query-context-show QUERY_ID=<id>"; exit 2; }
	$(POE) query-context-show "$(QUERY_ID)"

# --- End-to-end checks ---

.PHONY: e2e-test
e2e-test: ensure-uv ## Run the end-to-end tests; they start their own containers (ARGS='-k <expr>' to filter)
	$(POE) e2e-test $(ARGS)

.PHONY: e2e-ingest
e2e-ingest: ## Start the stack, ingest one Markdown file through the API, then stop the stack
	./scripts/run_e2e_ingestion.sh

.PHONY: e2e-compare-backends
e2e-compare-backends: ## Start the stack and compare deterministic and Ollama answers to one question
	./scripts/compare_answer_backends.sh

# --- Docs ---

.PHONY: docs-workstream-new
docs-workstream-new: ## Create a docs workstream (TYPE=<work_type> SLUG=<slug>)
	@test -n "$(TYPE)" -a -n "$(SLUG)" || { \
		echo "Usage: make docs-workstream-new TYPE=<work_type> SLUG=<slug>" >&2; \
		exit 2; \
	}
	@docs/harness/scripts/new-workstream.sh "$(TYPE)" "$(SLUG)"

# --- Aliases for old names ---

.PHONY: $(ALIAS_TARGETS)
install-git-hooks: setup-hooks ## Alias for setup-hooks
workstream-new: ## Alias for docs-workstream-new (type=<work_type> slug=<slug>)
	@$(MAKE) --no-print-directory docs-workstream-new TYPE="$(or $(type),$(TYPE))" SLUG="$(or $(slug),$(SLUG))"
docker-build: stack-build ## Alias for stack-build
docker-up: stack-up ## Alias for stack-up
docker-up-build: stack-up ## Alias for stack-up
docker-down: stack-down ## Alias for stack-down
docker-clean: stack-clean ## Alias for stack-clean
docker-logs: ## Alias for stack-logs ARGS=api
	@$(MAKE) --no-print-directory stack-logs ARGS=api
docker-log-index: stack-log-paths ## Alias for stack-log-paths
docker-db-shell: db-shell ## Alias for db-shell
observability-up-build: observability-up ## Alias for observability-up
