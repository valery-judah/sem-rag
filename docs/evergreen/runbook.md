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
make sync-llm
make sync-mac
make install
make run-api
make run-worker
make docker-up-build
make docker-smoke
make test-e2e
```

Lifecycle metadata migrations use Alembic and `.env`:

```bash
make migrate
make db-revision MESSAGE="add lifecycle index"
```

Internal upload app:
```bash
make run-api
```

Internal lifecycle worker:
```bash
export DOC_FORGE_WORKER_POLL_SECONDS=0.25
make run-worker
```

Docker-backed local stack:
```bash
export DOC_FORGE_UID="$(id -u)"
export DOC_FORGE_GID="$(id -g)"
make docker-up-build
make docker-ps
make docker-smoke
make docker-logs
```

Additional checks:
```bash
make fmt
make fmt-check
make lint
make type
make test
make test-e2e
make smoke-llm
make smoke-mac
DOC_FORGE_E2E_VERBOSE=1 make test-e2e
make verify
```

`make db-revision` creates a new revision file under `src/doc_forge/persistence/migrations/versions/`. Schema changes to lifecycle metadata should update both the SQLAlchemy table definitions and a reviewed Alembic revision.

## Internal Lifecycle Runtime
- `make run-api` runs the internal FastAPI lifecycle app with upload, status, retry, retrieval-smoke, health, and artifact-inspection routes.
- `make run-worker` runs the queue-draining lifecycle worker that advances documents from `REGISTERED` to `READY`.
- `make test-e2e` runs the docker-backed end-to-end document lifecycle suite under `tests/e2e/`.
- `DOC_FORGE_E2E_VERBOSE=1 make test-e2e` enables step-by-step e2e progress logs plus richer failure diagnostics.
- `POST /internal/run-next-job` exists for tests and local debug; normal local operation should prefer the worker loop.
- `make docker-up-build` starts the local Postgres, API, and worker stack defined in `docker-compose.yml`.
- In Docker Compose, the `api` and `worker` runtimes self-apply Alembic migrations at startup before serving traffic or draining jobs.
- `make docker-smoke` waits for the Compose API container to become healthy, then verifies that `/readyz` can reach the configured database and write under `DOC_FORGE_ARTIFACT_ROOT`.

## Database Migrations
- Alembic is the standard migration interface for lifecycle metadata tables.
- `DATABASE_URL` is the canonical database URL input for migration commands.
- `DOC_FORGE_AUTO_MIGRATE` is an internal runtime switch that enables lock-protected startup migrations for containerized `api` and `worker` processes.
- `DOC_FORGE_ARTIFACT_ROOT` is the internal runtime root for raw and intermediate artifact files used by the upload app.
- `DOC_FORGE_WORKER_POLL_SECONDS` controls idle sleep time for the internal worker loop.
- `DOC_FORGE_EMBEDDING_BACKEND` selects the embedding adapter. Supported values are `deterministic` and `sentence-transformers`. The default is `deterministic`.
- `DOC_FORGE_EMBEDDING_MODEL` sets the optional sentence-transformers model identifier. It is only used when `DOC_FORGE_EMBEDDING_BACKEND=sentence-transformers`.
- `DOC_FORGE_ANSWER_GENERATOR_BACKEND` selects the Stage 7 answer generator. Supported values are `deterministic` and `mlx`. The default is `deterministic`.
- `DOC_FORGE_ANSWER_GENERATOR_MODEL` sets the optional Apple Silicon generation model identifier. It is only used when `DOC_FORGE_ANSWER_GENERATOR_BACKEND=mlx`.
- `DOC_FORGE_ANSWER_GENERATOR_MAX_NEW_TOKENS` and `DOC_FORGE_ANSWER_GENERATOR_TEMPERATURE` control the optional MLX generation path.
- `DOC_FORGE_UID` and `DOC_FORGE_GID` let the compose services run as a non-root user that can still write to the bind-mounted `./data` artifact root.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`, and `PORT` are the compose-level defaults for the local Docker stack.
- `doc_forge.persistence.apply_migrations(...)` remains available as an internal helper for tests and bootstrapping, but normal repo operations should use Alembic commands.
- Postgres `docker-entrypoint-initdb.d` SQL bootstrap scripts are not the canonical schema path for lifecycle metadata; Alembic remains the single schema authority.
- The current Alembic scope covers lifecycle metadata plus ingestion/indexing persistence: `documents`, `lifecycle_events`, `document_jobs`, `sections`, `chunks`, `index_entries`, and `chunk_embeddings`.
- The SQLite compatibility seam for `Document`, `Section`, and `Chunk` remains in place and is not yet migrated into Alembic-managed runtime tables.

## Troubleshooting
- If imports fail, run `make sync` and `make install`.
- If optional model-backed embeddings or Apple Silicon generation fail to import, run `make sync-llm` or `make sync-mac` and verify the corresponding smoke target.
- If validation disagrees across environments, re-run the standard `fmt-check`, `lint`, `type`, `test`, and `verify` targets. Use `fmt` only when you want to apply automatic fixes.
- If Alembic commands fail immediately, verify that `DATABASE_URL` is set and points at a reachable database.
- If you encounter database authentication errors when connecting local processes to the Docker stack, run `make docker-clean` to wipe stale volumes and reset the credentials, then `make docker-up-build`.
- If the internal lifecycle app or worker fails at startup, verify `DATABASE_URL`, `DOC_FORGE_ARTIFACT_ROOT`, and migrations first.
- If the Docker stack cannot write artifacts as a non-root user, export `DOC_FORGE_UID` and `DOC_FORGE_GID` before `make docker-up-build`, then clean up any stale root-owned files under `./data`.
- If a doc describes ingestion, parsing, or grounded answering as already implemented, reconcile it with `docs/evergreen/architecture.md` and the actual code before treating it as current behavior.

## Escalation / Ownership
- Durable repo and product truth belongs in `docs/evergreen/`.
- Time-scoped investigation and implementation planning can live under `docs/workstreams/`.
- Long-lived cross-cutting decisions belong in `docs/adrs/`.
- Repo-specific templates and playbooks live in `docs/harness/`.
