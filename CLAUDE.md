# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Canonical repo instructions live in `AGENTS.md`. If this file conflicts with `AGENTS.md`, follow `AGENTS.md`.

## Read First

Use these docs in order:

1. `AGENTS.md` for repo workflow rules, validation expectations, and hard constraints
2. `docs/mvp-1.md` for the MVP pipeline shape, invariants, and milestones
3. `ARCHITECTURE.md` for the current codebase map and dependency directions
4. `docs/README.md` for the docs index and feature-doc routing
5. `docs/features/*/01_rfc.md` for feature-local normative behavior

## Claude Shortcuts

All Python commands use `uv`. Prefer `make` targets:

```bash
make sync      # Install/sync dependencies
make install   # Editable install
make test      # Run pytest
make fmt       # Format + autofix (ruff)
make lint      # Lint check (ruff)
make type      # Type check (mypy)
make check     # All checks: fmt + lint + type + test
make run       # Run CLI demo
```

Targeted test commands:

- `uv run pytest tests/parsers/test_models.py -v`
- `uv run pytest tests/parsers/test_models.py::test_name -v`

## Routing

This file is a convenience entrypoint, not a second source of truth.

- Use `docs/mvp-1.md` for system shape and milestone sequencing
- Use `docs/features/*/01_rfc.md` for normative feature behavior
- Use `ARCHITECTURE.md` for module boundaries and dependency directions
- Use `docs/README.md`, `docs/PIPELINE.md`, and `docs/PLANS.md` as routing docs

## Minimal Repo Map

- `src/docforge/connectors/`: source-document contracts and connector implementations
- `src/docforge/parsers/`: canonical parsing and PDF-hybrid parsing work
- `src/docforge/segmentation.py`: segmentation logic for parsed output
- `src/docforge/retrieval.py` and `src/docforge/cli.py`: lightweight retrieval demo surface
- `docs/features/`: feature-level RFCs, designs, and workplans
