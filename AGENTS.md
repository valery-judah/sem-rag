# Agent Contract For This Repository

This file is the repo entry point for agents. It is a routing layer, not the full handbook.

## Repo Purpose

`parity` is a minimal question-answering MVP scaffold. The current runtime surface is small and centered on a retrieval demo:

- `src/parity/retrieval.py`: in-memory `SemanticIndex`
- `src/parity/cli.py`: CLI demo over a small hard-coded corpus

...

## Agent Quick Routes

Authority rule:
- `docs/evergreen/`: Canonical
- `docs/delivery/`: Reference only
- `docs/workstreams/`: Execution history

Product Scope:
- `docs/evergreen/mvp.md`: Canonical. Product north star and scope boundary.

Implementation Truth:
- `docs/evergreen/architecture.md`: Canonical. Current repo shape and implementation gap.

Stable Interfaces:
- `docs/evergreen/api-contracts.md`: Canonical. Stable runtime interfaces that exist today.

Commands And Validation:
- `docs/evergreen/runbook.md`: Canonical. Local operation guidance and standard commands.

Evaluation Docs:
- `docs/README.md`: Canonical. Docs index and topic-based routes.
- `docs/evergreen/eval-vocabulary.md`: Canonical. Evaluation glossary, term normalization, and layer names.
- `docs/evergreen/eval-support-semantics.md`: Canonical. Support-state criteria, citation expectations, and abstention rules.
- `docs/evergreen/eval-scenario-taxonomy.md`: Canonical. Scenario classes and classification rules.
- `docs/evergreen/eval-failure-taxonomy.md`: Canonical. Failure classes and classification rules.

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

This section is a canonical-doc inventory, not a second routing block. Use `Agent Quick Routes` above for navigation.

- `docs/evergreen/mvp.md`: Canonical. Product north star and scope boundary.
- `docs/evergreen/architecture.md`: Canonical. Current repo shape and implementation gap.
- `docs/evergreen/api-contracts.md`: Canonical. Stable runtime interfaces that exist today.
- `docs/evergreen/runbook.md`: Canonical. Local operation guidance and standard commands.
- `docs/README.md`: Canonical. Docs index and topic-based routes.

`docs/delivery/` may contain planning, architecture, or workflow drafts, but it is not the canonical source of product scope.

## Hard Constraints

- Keep `uv.lock` committed and up to date after dependency changes; do not edit it manually.
- Treat `docs/evergreen/mvp.md` as the sole MVP north star for product scope and boundary decisions.
- Do not describe target MVP capabilities as already implemented unless the codebase actually exposes them.
