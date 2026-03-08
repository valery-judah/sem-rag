# Runbook

## Purpose
This file captures durable operational guidance for the current repository. Use it for common local commands, quick verification, and basic troubleshooting of the retrieval demo package.

## When To Use
- Bootstrapping the repo locally
- Running the standard validation loop
- Checking which local commands are part of the normal workflow

## Local Setup / Common Commands
```bash
make sync
make install
make run
```

Additional checks:
```bash
make fmt
make lint
make type
make test
```

## What `make run` Does
- Installs the package in editable mode through the `install` dependency in `Makefile`
- Runs `python -m parity.cli`
- Prints ranked matches from a small hard-coded document list

## Troubleshooting
- If imports fail, run `make sync` and `make install`.
- If validation disagrees across environments, re-run the standard `fmt`, `lint`, `type`, and `test` targets.
- If `make run` changes behavior, inspect `src/parity/cli.py` and `src/parity/retrieval.py` first because they define the current runtime surface.
- If a doc describes ingestion, parsing, or grounded answering as already implemented, reconcile it with `docs/evergreen/architecture.md` and the actual code before treating it as current behavior.

## Escalation / Ownership
- Durable repo and product truth belongs in `docs/evergreen/`.
- Time-scoped investigation and implementation planning can live under `docs/workstreams/`.
- Long-lived cross-cutting decisions belong in `docs/adrs/`.
- Repo-specific templates and playbooks live in `docs/harness/`.
