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
- Prefer `make` targets when available.
- If a target does not exist, use `uv run <tool>`.
- Do not use `pip`, `python -m pip`, `poetry`, or `pipenv` directly.
- `make sync`
- `make install`
- `make run`
- `make fmt`
- `make fmt-check`
- `make lint`
- `make type`
- `make test`
- `make verify`
- `make check`

## Validation
- Docs-only change: no mandatory validation; run targeted checks only if docs affect commands or generated artifacts.
- Code change without public contract impact: `make test`
- Package or API behavior change: `make fmt-check`, `make lint`, `make type`, `make test`
- If uncertain: `make verify`
- Keep `uv.lock` committed and updated after dependency changes; do not edit it manually.
- Do not describe capabilities as implemented unless the codebase actually exposes them.
