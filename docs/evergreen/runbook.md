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

Lifecycle metadata migrations use Alembic with `DATABASE_URL`:

```bash
export DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/parity
make migrate
make db-revision MESSAGE="add lifecycle index"
```

Internal upload app:
```bash
export DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/parity
export PARITY_ARTIFACT_ROOT=./data
uv run uvicorn parity.app.api:app --reload
```

Additional checks:
```bash
make fmt
make fmt-check
make lint
make type
make test
make verify
```

`make db-revision` creates a new revision file under `src/parity/persistence/migrations/versions/`. Schema changes to lifecycle metadata should update both the SQLAlchemy table definitions and a reviewed Alembic revision.

## What `make run` Does
- Installs the package in editable mode through the `install` dependency in `Makefile`
- Runs `python -m parity.cli`
- Prints ranked matches from a small hard-coded document list

## Database Migrations
- Alembic is the standard migration interface for lifecycle metadata tables.
- `DATABASE_URL` is the canonical database URL input for migration commands.
- `PARITY_ARTIFACT_ROOT` is the internal runtime root for raw and intermediate artifact files used by the upload app.
- `parity.persistence.apply_migrations(...)` remains available as an internal helper for tests and bootstrapping, but normal repo operations should use Alembic commands.
- The current Alembic scope is limited to lifecycle metadata tables: `documents`, `lifecycle_events`, and `document_jobs`.
- The SQLite compatibility seam for `Document`, `Section`, and `Chunk` remains in place and is not yet migrated into Alembic-managed runtime tables.

## Troubleshooting
- If imports fail, run `make sync` and `make install`.
- If validation disagrees across environments, re-run the standard `fmt-check`, `lint`, `type`, `test`, and `verify` targets. Use `fmt` only when you want to apply automatic fixes.
- If Alembic commands fail immediately, verify that `DATABASE_URL` is set and points at a reachable database.
- If the internal upload app fails at startup, verify both `DATABASE_URL` and `PARITY_ARTIFACT_ROOT`, then ensure migrations have been applied before posting documents.
- If `make run` changes behavior, inspect `src/parity/cli.py` and `src/parity/retrieval.py` first because they define the current runtime surface.
- If a doc describes ingestion, parsing, or grounded answering as already implemented, reconcile it with `docs/evergreen/architecture.md` and the actual code before treating it as current behavior.

## Escalation / Ownership
- Durable repo and product truth belongs in `docs/evergreen/`.
- Time-scoped investigation and implementation planning can live under `docs/workstreams/`.
- Long-lived cross-cutting decisions belong in `docs/adrs/`.
- Repo-specific templates and playbooks live in `docs/harness/`.
