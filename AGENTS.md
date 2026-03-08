# Agent Contract For This Repository

This file is the repo entry point for agents. It is a routing layer, not the full handbook.

## Repo Purpose

`parity` is a minimal question-answering MVP scaffold. The current runtime surface is small and centered on a retrieval demo:

- `src/parity/retrieval.py`: in-memory `SemanticIndex`
- `src/parity/cli.py`: CLI demo over a small hard-coded corpus

The broader product target is defined in `docs/evergreen/mvp.md`. That target includes document ingestion, normalization, retrieval, and source-grounded answering, but those flows are not implemented in the current codebase yet.

Start with:

- product north star: `docs/evergreen/mvp.md`
- repo/code map: `docs/evergreen/architecture.md`
- stable interfaces: `docs/evergreen/api-contracts.md`
- docs map: `docs/README.md`

## Required Commands And Validation Matrix

### Workflow rules
- Use `uv` for all Python-related commands.
- Do not use `pip`, `python -m pip`, `poetry`, or `pipenv` directly.
- Prefer `make` targets when available.
- If a task is not in `Makefile`, run it via `uv run <tool>`.

### Standard commands
- Sync dependencies: `make sync`
- Editable install: `make install`
- Run demo CLI: `make run`
- Format: `make fmt`
- Lint: `make lint`
- Type check: `make type`
- Tests: `make test`

### Validation matrix
- Docs-only change: no mandatory test run; run targeted checks only if docs affect generated artifacts or commands.
- Code change without public contract impact: `make test`
- Package/API behavior change: `make fmt`, `make lint`, `make type`, `make test`

## Canonical Docs

- `docs/evergreen/mvp.md`: MVP product definition and scope
- `docs/evergreen/architecture.md`: current repo/module boundaries and target-state gap
- `docs/evergreen/api-contracts.md`: stable runtime interfaces that exist today
- `docs/evergreen/runbook.md`: durable local operation guidance
- `docs/README.md`: documentation index

## Hard Constraints

- Keep `uv.lock` committed and up to date after dependency changes; do not edit it manually.
- Treat `docs/evergreen/mvp.md` as the MVP north star for product scope and boundary decisions.
- Do not describe target MVP capabilities as already implemented unless the codebase actually exposes them.
