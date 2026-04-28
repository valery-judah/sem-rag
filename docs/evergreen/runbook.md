# Runbook

## Purpose
This file captures durable operational guidance for the current repository. Use it for common local commands, lifecycle runtime startup, quick verification, and troubleshooting.

For the split runtime-versus-observability startup model, eval-focused run
flows, and where logs plus query/eval data are collected, also use
[`observability-operations.md`](./observability-operations.md).

## When To Use
- Bootstrapping the repo locally
- Running the standard validation loop
- Checking which local commands are part of the normal workflow

Command model:
- `uv run poe <task>` for Python developer tasks
- `make <target>` for Docker, Compose, observability, docs harness helpers,
  and other local DevEx wrappers
- Host-side `uv` commands use the repo-local cache configured in `uv.toml`
  at `./.tmp_uv_cache`

## Local Setup / Common Commands
```bash
uv sync
uv sync --group llm
uv sync --group llm --group mac
uv run poe run-api
uv run poe run-worker
uv run poe observability-loader-scan
uv run poe test-e2e
uv run poe collect-query-context <query_id>
uv run poe show-query-context <query_id>
uv run poe clean --dry-run
uv run poe clean
make docker-up-build
make docker-log-index
make observability-up-build
make observability-down
make workstream-new type=feature slug=my-feature
```

Lifecycle metadata migrations use Alembic and `.env`:

```bash
uv run poe migrate
uv run poe db-revision message="add lifecycle index"
```

Internal upload app:
```bash
uv run poe run-api
```

Internal lifecycle worker:
```bash
export DOC_FORGE_WORKER_POLL_SECONDS=0.1
uv run poe run-worker
```

Docker-backed local stack:
```bash
export DOC_FORGE_UID="$(id -u)"
export DOC_FORGE_GID="$(id -g)"
make docker-up-build
make docker-logs
make docker-log-index
uv run poe collect-query-context qry-123
uv run poe show-query-context qry-123
make observability-up-build
make observability-down
```

Additional checks:
```bash
uv run poe fmt
uv run poe fmt-check
uv run poe lint
uv run poe type
uv run poe test
uv run poe test-e2e
uv run poe smoke-llm
uv run poe smoke-mac
uv run poe clean --dry-run
DOC_FORGE_E2E_VERBOSE=1 uv run poe test-e2e
uv run poe verify
```

`uv run poe db-revision` creates a new revision file under `src/doc_forge/persistence/migrations/versions/`. Schema changes to lifecycle metadata should update both the SQLAlchemy table definitions and a reviewed Alembic revision.

## Local HTTP Runtime
- `uv run poe run-api` runs the stable localhost FastAPI service at `http://127.0.0.1:8000` with health, readiness, document lifecycle, query, and review routes.
- `http://127.0.0.1:8000/docs` serves the Swagger UI only when `DOC_FORGE_ENABLE_SWAGGER=true`; `DOC_FORGE_ENVIRONMENT=dev` alone does not enable it.
- `http://127.0.0.1:8000/openapi.json` serves the live mounted-app schema on the same condition. That schema includes the internal-only debug and operator routes mounted in the same app, so use [`docs/evergreen/api-contracts.md`](./api-contracts.md) for the stable public subset.
- `uv run poe run-worker` runs the queue-draining lifecycle worker that advances documents from `REGISTERED` to `READY`.
- `uv run poe test-e2e` runs the docker-backed end-to-end document lifecycle suite under `tests/e2e/`.
- `DOC_FORGE_E2E_VERBOSE=1 uv run poe test-e2e` enables step-by-step e2e progress logs plus richer failure diagnostics.
- `POST /retrieval/query` remains a local retrieval smoke/debug route rather than part of the stable public contract.
- `POST /internal/run-next-job` exists for tests and local debug; normal local operation should prefer the worker loop.
- `make docker-up-build` starts the local Postgres, API, and worker stack defined in `docker-compose.yml`.
- On `Darwin arm64`, `make docker-up-build` and `uv run poe test-e2e` prefer host Ollama at `http://host.docker.internal:11434` with `llama3.2:1b` when the host Ollama service is reachable; other hosts keep deterministic answer generation by default.
- `make observability-up-build` starts the separate central observability stack defined in `docker-compose.observability.yml`.
- `make observability-down` stops the separate observability stack.
- `uv run poe observability-loader-scan` runs a one-shot metadata scan over existing query bundles and indexes them into the observability Postgres store.
- `uv run poe clean --dry-run` shows which generated caches, lifecycle artifacts, query bundles, archived logs, the repo-local uv cache at `./.tmp_uv_cache`, and tool-local virtual environments under `tools/` would be removed.
- `uv run poe clean` removes that generated local state while preserving user-provided inputs such as files directly under `data/` and non-generated files under `tools/` by default. Pass `--include-model-cache` if you also want to remove `data/huggingface/`.
- In Docker Compose, the `api` and `worker` runtimes self-apply Alembic migrations at startup before serving traffic or draining jobs.
- Container JSON logs are archived under `data/logs/compose/runs/<run_id>/` with stable links at `data/logs/compose/latest/`.
- Docker-backed e2e runs archive per-scenario JSON logs under `data/logs/e2e/runs/<session_id>/<test_id>/` with stable links under `data/logs/e2e/latest/`.
- `make docker-log-index` prints the main repo-local archive locations for Compose and e2e logs.
- `uv run poe collect-query-context <query_id>` collects a reusable query bundle under `data/context/queries/<query_id>/`.
- `uv run poe show-query-context <query_id>` prints the bundle root plus the resolved summary, citations, trace, replay, log, and eval paths for that query when available.
- For a step-by-step guide on running a manual end-to-end ingestion test locally, see [`manual-e2e.md`](./manual-e2e.md).

## Tracing And Context
- `logs` are stream-oriented container events archived under `data/logs/`; use them to inspect request, worker, and review activity around a query.
- `trace` is the durable per-query stage record persisted in `query_stage_traces` and exposed through `/queries/{query_id}/trace`.
- `replay` is the frozen query input bundle reconstructed from persisted state; query context collection writes it to `data/context/queries/<query_id>/replay.json`.
- Query-centric bundles under `data/context/queries/<query_id>/` index those assets together with `manifest.json`, filtered `logs/query-events.jsonl`, and any available eval metadata.
- The central observability stack ingests those filesystem outputs rather than replacing them:
  - Postgres indexes query/eval bundle metadata
  - Loki centralizes JSON service logs
  - Grafana provides the common UI

## Database Migrations
- Alembic is the standard migration interface for lifecycle metadata tables.
- `DATABASE_URL` is the canonical database URL input for migration commands.
- `DOC_FORGE_AUTO_MIGRATE` is an internal runtime switch that enables lock-protected startup migrations for containerized `api` and `worker` processes.
- `DOC_FORGE_ARTIFACT_ROOT` is the internal runtime root for raw and intermediate artifact files used by the upload app.
- `DOC_FORGE_WORKER_POLL_SECONDS` controls idle sleep time for the internal worker loop.
- `DOC_FORGE_EMBEDDING_BACKEND` selects the embedding adapter. Supported values are `deterministic` and `sentence-transformers`. The default is `sentence-transformers`.
- `DOC_FORGE_EMBEDDING_MODEL` sets the optional sentence-transformers model identifier. It is only used when `DOC_FORGE_EMBEDDING_BACKEND=sentence-transformers`.
- `DOC_FORGE_ANSWER_GENERATOR_BACKEND` selects the Stage 7 answer generator. Supported values are `deterministic`, `mlx`, and `ollama`. The process default remains `deterministic`.
- `DOC_FORGE_ANSWER_GENERATOR_MODEL` sets the optional generation model identifier. It is used by both `mlx` and `ollama`.
- `DOC_FORGE_ANSWER_GENERATOR_MAX_NEW_TOKENS` and `DOC_FORGE_ANSWER_GENERATOR_TEMPERATURE` control the optional MLX and Ollama generation paths.
- `OLLAMA_BASE_URL` sets the Ollama HTTP endpoint for Docker-backed local and e2e runs. Apple Silicon Docker defaults point containers at `http://host.docker.internal:11434` when host Ollama is available.
- `DOC_FORGE_UID` and `DOC_FORGE_GID` let the compose services run as a non-root user that can still write to the bind-mounted `./data` artifact root.
- `DOC_FORGE_JSON_LOG_PATH` is an internal container-only path used to duplicate stdout JSON logs into repo-local JSONL archives.
- `DOC_FORGE_LOG_RUN_ID` is the optional compose run identifier used for `data/logs/compose/runs/<run_id>/`.
- `DOC_FORGE_OBSERVABILITY_DATABASE_URL` is the optional direct database URL for the observability metadata store and loader CLI.
- `OBSERVABILITY_POSTGRES_DB`, `OBSERVABILITY_POSTGRES_USER`, `OBSERVABILITY_POSTGRES_PASSWORD`, `OBSERVABILITY_POSTGRES_PORT`, `OBSERVABILITY_LOKI_PORT`, and `OBSERVABILITY_GRAFANA_PORT` control the separate observability stack.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`, and `PORT` are the compose-level defaults for the local Docker stack.
- `doc_forge.persistence.apply_migrations(...)` remains available as an internal helper for tests and bootstrapping, but normal repo operations should use Alembic commands.
- Postgres `docker-entrypoint-initdb.d` SQL bootstrap scripts are not the canonical schema path for lifecycle metadata; Alembic remains the single schema authority.
- The current Alembic scope covers lifecycle metadata plus ingestion/indexing persistence: `documents`, `lifecycle_events`, `document_jobs`, `sections`, `chunks`, `index_entries`, and `chunk_embeddings`.
- The SQLite compatibility seam for `Document`, `Section`, and `Chunk` remains in place and is not yet migrated into Alembic-managed runtime tables.

## Troubleshooting
- If imports fail, run `uv sync`.
- If optional model-backed embeddings or Apple Silicon generation fail to import, run `uv sync --group llm` or `uv sync --group llm --group mac` and verify the corresponding smoke target.
- If Apple Silicon Docker runs stay deterministic, confirm host Ollama is reachable at `http://127.0.0.1:11434/api/tags`; `make docker-up-build` and `uv run poe test-e2e` only switch to Ollama when that health check succeeds.
- If you want Docker-backed local runs to use the Compose Ollama container instead of host Ollama, start with `COMPOSE_PROFILES=ollama DOC_FORGE_ANSWER_GENERATOR_BACKEND=ollama OLLAMA_BASE_URL=http://ollama:11434 make docker-up-build`.
- If you want to verify GPU-backed local generation on Apple Silicon, run one query after `make docker-up-build`, confirm `ollama ps` shows `llama3.2:1b` on `100% GPU`, and confirm archived API logs contain `event=\"llm generated\"` with `generator_backend=\"ollama\"`.
- If validation disagrees across environments, re-run the standard `fmt-check`, `lint`, `type`, `test`, and `verify` targets. Use `fmt` only when you want to apply automatic fixes.
- If Alembic commands fail immediately, verify that `DATABASE_URL` is set and points at a reachable database.
- If you encounter database authentication errors when connecting local processes to the Docker stack, run `make docker-clean` to wipe stale volumes and reset the credentials, then `make docker-up-build`.
- If the internal lifecycle app or worker fails at startup, verify `DATABASE_URL`, `DOC_FORGE_ARTIFACT_ROOT`, and migrations first.
- If the Docker stack cannot write artifacts as a non-root user, export `DOC_FORGE_UID` and `DOC_FORGE_GID` before `make docker-up-build`, then clean up any stale root-owned files under `./data`.
- If archived container logs are missing, verify that `data/logs/` is writable and that the container run mounted `/logs` successfully.
- If a query bundle is incomplete, inspect `data/context/queries/<query_id>/manifest.json`; missing components are listed explicitly under `missing_assets`.
- If the observability stack shows no runs, start with `uv run poe observability-loader-scan` and confirm `data/context/queries/` contains collected bundles.
- If Grafana starts but shows no logs, confirm Vector has access to `data/logs/` and that Loki is reachable at `http://127.0.0.1:${OBSERVABILITY_LOKI_PORT:-3100}`.
- If a doc describes ingestion, parsing, or grounded answering as already implemented, reconcile it with `docs/evergreen/architecture.md` and the actual code before treating it as current behavior.

## Escalation / Ownership
- Durable repo and product truth belongs in `docs/evergreen/`.
- Time-scoped investigation and implementation planning can live under `docs/workstreams/`.
- Long-lived cross-cutting decisions belong in `docs/adrs/`.
- Repo-specific templates and playbooks live in `docs/harness/`.
