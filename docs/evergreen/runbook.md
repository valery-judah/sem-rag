# Runbook

## Purpose
This file captures durable operational guidance for the current repository. Use it for common local commands, lifecycle runtime startup, quick verification, and troubleshooting.

## When To Use
- Bootstrapping the repo locally
- Running the standard validation loop
- Checking which local commands are part of the normal workflow

## Local Setup / Common Commands
```bash
make sync
make install
make run
make run-api
make run-worker
make test-e2e
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
make run-api
```

Internal lifecycle worker:
```bash
export DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/parity
export PARITY_ARTIFACT_ROOT=./data
export PARITY_WORKER_POLL_SECONDS=0.25
make run-worker
```

Additional checks:
```bash
make fmt
make fmt-check
make lint
make type
make test
make test-e2e
make verify
```

Manual Docker stack:
```bash
docker compose up --build
```

`make db-revision` creates a new revision file under `src/parity/persistence/migrations/versions/`. Schema changes to lifecycle metadata should update both the SQLAlchemy table definitions and a reviewed Alembic revision.

## What `make run` Does
- Installs the package in editable mode through the `install` dependency in `Makefile`
- Runs `python -m parity.cli`
- Prints ranked matches from a small hard-coded document list

## Internal Lifecycle Runtime
- `make run-api` runs the internal FastAPI lifecycle app with upload, status, retry, retrieval-smoke, health, and artifact-inspection routes.
- `make run-worker` runs the queue-draining lifecycle worker that advances documents from `REGISTERED` to `READY`.
- `make test-e2e` runs the docker-backed end-to-end Markdown lifecycle suite under `tests/e2e/`.
- `POST /internal/run-next-job` exists for tests and local debug; normal local operation should prefer the worker loop.
- `docker compose up --build` starts the local Postgres, migration, API, and worker stack defined in `docker-compose.yml`.

## Database Migrations
- Alembic is the standard migration interface for lifecycle metadata tables.
- `DATABASE_URL` is the canonical database URL input for migration commands.
- `PARITY_ARTIFACT_ROOT` is the internal runtime root for raw and intermediate artifact files used by the upload app.
- `PARITY_WORKER_POLL_SECONDS` controls idle sleep time for the internal worker loop.
- `parity.persistence.apply_migrations(...)` remains available as an internal helper for tests and bootstrapping, but normal repo operations should use Alembic commands.
- The current Alembic scope covers lifecycle metadata plus ingestion/indexing persistence: `documents`, `lifecycle_events`, `document_jobs`, `sections`, `chunks`, `index_entries`, and `chunk_embeddings`.
- The SQLite compatibility seam for `Document`, `Section`, and `Chunk` remains in place and is not yet migrated into Alembic-managed runtime tables.

## Troubleshooting
- If imports fail, run `make sync` and `make install`.
- If validation disagrees across environments, re-run the standard `fmt-check`, `lint`, `type`, `test`, and `verify` targets. Use `fmt` only when you want to apply automatic fixes.
- If Alembic commands fail immediately, verify that `DATABASE_URL` is set and points at a reachable database.
- If the internal lifecycle app or worker fails at startup, verify `DATABASE_URL`, `PARITY_ARTIFACT_ROOT`, and migrations first.
- If `make run` changes behavior, inspect `src/parity/cli.py` and `src/parity/retrieval.py` first because they define the current runtime surface.
- If a doc describes ingestion, parsing, or grounded answering as already implemented, reconcile it with `docs/evergreen/architecture.md` and the actual code before treating it as current behavior.

## Escalation / Ownership
- Durable repo and product truth belongs in `docs/evergreen/`.
- Time-scoped investigation and implementation planning can live under `docs/workstreams/`.
- Long-lived cross-cutting decisions belong in `docs/adrs/`.
- Repo-specific templates and playbooks live in `docs/harness/`.
