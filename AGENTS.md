# Agent Contract For This Repository

This file is the repo entry point for agents. It is a routing layer, not the full handbook.

## Repo Purpose

`docforge` is a semantic-pipeline MVP for turning raw internal documents into queryable knowledge artifacts. The current repo contains:

- source-document contracts and connectors in `src/docforge/connectors/`
- canonical parsing and PDF-hybrid parsing work in `src/docforge/parsers/`
- a small retrieval demo in `src/docforge/retrieval.py` and `src/docforge/cli.py`
- feature-spec documentation in `docs/features/`

Start with:

- product/system north star: `docs/mvp-1.md`
- repo/code map: `ARCHITECTURE.md`
- pipeline navigation: `docs/PIPELINE.md`

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
- Parser/schema/logic change: `make fmt`, `make lint`, `make type`, `make test`

## Canonical Docs

- `docs/mvp-1.md`: MVP semantic-pipeline contract and milestone map
- `ARCHITECTURE.md`: current repo/module boundaries and dependency directions
- `docs/README.md`: documentation index
- `docs/PIPELINE.md`: map from `mvp-1.md` components to code and feature docs
- `docs/PLANS.md`: where active execution plans and workplans live
- `docs/00_playbook.md`: reusable feature-doc workflow
- `docs/01_artifact_contracts.md`: authority rules for feature artifacts
- `docs/runbooks/local-dev.md`: future-facing local runtime scaffold
- `docs/generated/README.md`: reserved location for future generated references

## Hard Constraints

- Keep `uv.lock` committed and up to date after dependency changes; do not edit it manually.
- Treat `docs/mvp-1.md` as the MVP north star for pipeline scope and component boundaries.
- Treat `docs/features/*/01_rfc.md` as the normative contract for feature-specific behavior.
- Treat `00_context.md`, `03_design.md`, and `04_workplan.md` as supporting artifacts; do not move contract authority out of the RFC unless the docs are intentionally restructured together.
- New control-plane docs must summarize and route; they must not redefine schemas already owned by `docs/mvp-1.md` or feature RFCs.
