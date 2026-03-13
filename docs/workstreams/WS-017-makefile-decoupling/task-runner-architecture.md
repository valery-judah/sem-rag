# Task Runner Architecture

## Summary
The repository now uses a split task-runner model:

1. `uv` manages Python environments and executes tools.
2. `poethepoet` runs Python developer tasks through `uv run poe <task>`.
3. `Makefile` is reserved for local DevEx and infrastructure wrappers such as
   Docker, Docker Compose, and the observability stack.

This is the current repository architecture, not a proposal.

## Goals
- Keep Python workflows Python-native and cross-platform.
- Keep Docker and local infrastructure commands discoverable in one place.
- Avoid mixing packaging, Python tooling, and container orchestration concerns.
- Make the command model obvious for humans and agents.

## Current Structure

### `pyproject.toml`
`pyproject.toml` is the source of truth for:
- package metadata
- dependency groups
- tool configuration
- Poe bootstrap configuration

Current relevant sections:
- `[dependency-groups]`
  - includes `poethepoet` in `dev`
- `[tool.poe]`
  - includes `poe_tasks.toml`
  - loads `.env`
- `[tool.poe.env]`
  - defines default environment values used by Poe tasks

It does not contain the task catalog directly anymore.

### `poe_tasks.toml`
`poe_tasks.toml` is the dedicated task catalog for Python developer workflows.

Current task groups include:
- formatting and checks
  - `fmt`
  - `fmt-check`
  - `lint`
  - `type`
  - `test`
  - `test-e2e`
  - `verify`
  - `check`
- local runtime
  - `run-api`
  - `run-worker`
- database and migrations
  - `migrate`
  - `db-revision`
- repo maintenance
  - `secret-scan`
  - `secret-scan-staged`
  - `dead-code`
- context and observability helpers
  - `observability-loader-scan`
  - `collect-query-context`
  - `show-query-context`

All of these run through:
```bash
uv run poe <task>
```

### `Makefile`
`Makefile` is now intentionally narrow. It is the operator surface for local
DevEx and infrastructure wrappers only.

Current retained responsibilities:
- Docker image and stack operations
  - `docker-build`
  - `docker-up`
  - `docker-up-build`
  - `docker-down`
  - `docker-clean`
- observability stack operations
  - `observability-up`
  - `observability-up-build`
  - `observability-down`
- Docker-oriented inspection helpers
  - `docker-logs`
  - `docker-log-index`
  - `docker-db-shell`
- repo-level Git configuration
  - `install-git-hooks`

The `help` target explicitly tells users to run `uv run poe <task>` for Python
work.

## Command Model

### Use `uv run poe <task>` when the action is:
- Python formatting, linting, type checking, or tests
- local API or worker startup outside Docker
- Alembic migration work
- query context collection
- observability metadata rescans
- other Python-only developer tooling

Examples:
```bash
uv sync
uv run poe run-api
uv run poe run-worker
uv run poe test
uv run poe verify
uv run poe migrate
uv run poe collect-query-context qry-123
```

### Use `make <target>` when the action is:
- Docker or Docker Compose startup/shutdown
- local runtime stack management
- observability stack management
- Docker log inspection
- Docker database shell access

Examples:
```bash
make docker-up-build
make docker-logs
make docker-log-index
make observability-up-build
make observability-down
make docker-db-shell
```

## Why This Split
- `uv` and Poe are a better fit for Python-first workflows than shell-oriented
  Make targets.
- Poe tasks are easier to keep portable across local environments.
- The `Makefile` remains useful for operator-facing orchestration that is
  naturally shell and Docker oriented.
- The split reduces ambiguity:
  - Python task? use Poe.
  - Docker or local infrastructure? use Make.

## Key Implementation Choices

### Poe tasks live in a separate file
The task catalog was moved out of `pyproject.toml` into `poe_tasks.toml`.

Why:
- keeps `pyproject.toml` focused on packaging and tool configuration
- makes the task surface easier to scan
- prevents the main project config from becoming overloaded

### `uv sync` replaces ad hoc install commands
The preferred environment bootstrap is:
```bash
uv sync
```

Optional dependency groups are added explicitly when needed:
```bash
uv sync --group llm
uv sync --group llm --group mac
```

### Make remains a wrapper layer, not the Python task runner
The current repo still uses `make` because Docker and Compose workflows are
more readable there, but it is no longer the primary interface for Python work.

## Practical Consequences For Documentation
Docs should follow these rules:
- do not recommend `make fmt`, `make lint`, `make test`, `make run-api`, or
  `make run-worker`
- prefer `uv run poe <task>` for Python lifecycle and validation commands
- reserve `make` examples for Docker, observability, and DevEx wrappers
- keep the split explicit in operator docs so readers do not need to infer it

## Migration Outcome
The repository now has a stable three-part layout:

1. `pyproject.toml`
   - packaging, dependencies, tool configuration, Poe bootstrap
2. `poe_tasks.toml`
   - Python task definitions
3. `Makefile`
   - Docker and local infrastructure wrappers

That is the architecture the rest of the docs should describe.
