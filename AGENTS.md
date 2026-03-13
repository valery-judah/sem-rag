# Agent Contract

## Canonical sources
- `docs/evergreen/mvp.md` - product scope
- `docs/evergreen/architecture.md` - architecture and current repo shape
- `docs/evergreen/api-contracts.md` - stable runtime interfaces
- `docs/evergreen/runbook.md` - local commands and operation
- `docs/README.md` - docs index

`docs/evergreen/` is canonical. `docs/delivery/` is reference-only. `docs/workstreams/` is history-only.

## Commands
- Use `uv` for Python-related commands.
- Use `uv run poe <task>` for Python developer tasks defined in `poe_tasks.toml`.
- Use `make` only for local DevEx and infrastructure wrappers such as Docker,
  Docker Compose, and observability stack operations.
- If a Python task is not defined in Poe, use `uv run <tool>`.
- Do not use `pip`, `python -m pip`, `poetry`, or `pipenv` directly.
- `uv sync`
- `uv sync --group llm`
- `uv sync --group llm --group mac`
- `uv run poe run-api`
- `uv run poe run-worker`
- `uv run poe fmt`
- `uv run poe fmt-check`
- `uv run poe lint`
- `uv run poe type`
- `uv run poe test`
- `uv run poe verify`
- `uv run poe check`
- `make docker-up-build`
- `make docker-smoke`
- `make docker-log-index`
- `make observability-up-build`
- `make observability-down`

## Validation
- Docs-only change: no mandatory validation; run targeted checks only if docs affect commands or generated artifacts.
- Code change: `uv run poe verify`

## Development Practices
- Save any temporary, exploratory, or developer-experience (devex) scripts into the `scripts/devex/` directory.

## Coding Conventions
- `docs/conventions/python-conventions.md` - coding standards and domain modeling
- `docs/conventions/python-logging.md` - logging, tracing, and dependency injection patterns
