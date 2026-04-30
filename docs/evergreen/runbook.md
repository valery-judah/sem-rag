# Runbook

`make help` lists every command. This runbook says when to use each one. Pass extra arguments
with `ARGS='...'`. For the observability stack, eval run flows, and where logs and query bundles
are saved, also see [`observability-operations.md`](./observability-operations.md).

## Command entry points

Make is the single entry point. Make targets call Poe tasks in `poe_tasks.toml` for Python work
and Docker Compose for containers. Poe task names use the same prefixes, so `make app-api` runs
`uv run poe app-api`.

| Prefix | Owns | Doesn't own |
| --- | --- | --- |
| `setup-`, `clean` | Dependency sync, optional dependency groups, the lock file, Git hooks, and removing generated local state | Starting processes |
| Checks: `fmt`, `fmt-check`, `lint`, `type`, `test`, `verify`, `secret-scan` | Formatting, lint, types, unit tests, and secret scans. Only `fmt` changes files | Docker and end-to-end tests |
| `app-` | The API and the worker on the host, in the foreground | The database and containers |
| `db-` | Alembic migrations against `DATABASE_URL`, and a psql shell in the stack's Postgres | Starting or stopping Postgres |
| `stack-` | The local Docker stack in `docker-compose.yml`: db, api, worker, and the optional Ollama container. `stack-up-db` starts only Postgres | The observability stack |
| `observability-` | The observability stack in `docker-compose.observability.yml`, and indexing query bundles into it | The local stack |
| `query-context-` | Collecting and showing one query's trace, replay, logs, and eval data | Starting services |
| `e2e-` | Docker-backed end-to-end tests and scenario scripts | Unit tests |
| `docs-` | Creating workstream folders from `docs/harness/` templates | Evergreen docs |

Old names still work as aliases and are listed at the end of `make help`: `docker-up-build`,
`docker-down`, `docker-logs`, `docker-log-index`, `workstream-new`, `install-git-hooks`, and
others.

Pick the lowest-level command that does the job. `stack-up` returns once the containers are
healthy, and `stack-down` keeps the database volume. `stack-clean` deletes it.

## Setup

```bash
make setup
```

`make setup` syncs dependencies into `.venv` and points Git at `.githooks/`. The pre-commit hook
runs `make secret-scan-staged`.

Optional dependency groups:

```bash
make setup-llm    # sentence-transformers for model-backed embeddings
make setup-mac    # also MLX for answer generation on Apple Silicon
```

Each command installs its groups and checks that they import. `make setup-sync` removes them
again.

## Validation

```bash
make verify
```

`make verify` runs `fmt-check`, `lint`, `type`, and `test` and stops at the first failure. Run one
step on its own with the target of the same name, and filter tests with `ARGS`, for example
`make test ARGS='-k lifecycle'`. `make fmt` fixes formatting and lint issues in place.

End-to-end tests build the `Dockerfile.e2e` image and start their own containers through
testcontainers, so they don't need the stack:

```bash
make e2e-test
DOC_FORGE_E2E_VERBOSE=1 make e2e-test
```

The verbose form prints each step and more detail on failure. Filter with `ARGS='-k <expr>'`. Each run saves per-scenario JSON
logs under `data/logs/e2e/runs/<session_id>/<test_id>/`, with links to the latest run under
`data/logs/e2e/latest/`.

Two scenario scripts start the stack and stop it when they finish, even on failure:

- `make e2e-ingest` uploads one Markdown file through the API and waits until it is ready.
- `make e2e-compare-backends` uploads sample documents and compares deterministic and Ollama
  answers to one question.

## Local Docker stack

```bash
make stack-up
make stack-status
make stack-logs
make stack-down
```

`make stack-up` builds the images and starts Postgres, the API, and the worker, then returns once
they are healthy. The API is on `http://127.0.0.1:8000`. The API and worker apply Alembic
migrations at startup. Make passes your user and group IDs as `DOC_FORGE_UID` and
`DOC_FORGE_GID`, so the containers can write to `./data`.

On Apple Silicon, `make stack-up` and `make e2e-test` use host Ollama at
`http://host.docker.internal:11434` with `llama3.2:1b` when it responds. Other hosts use
deterministic answers.

- `make stack-logs` prints recent logs for all services. Use `ARGS='api'` for one service or
  `ARGS='--follow'` to keep following.
- Container JSON logs are also saved under `data/logs/compose/runs/<run_id>/`, with links to the
  latest run under `data/logs/compose/latest/`. `make stack-log-paths` prints these locations.
- `make db-shell` opens psql in the stack's Postgres. Pass one query with
  `ARGS='-c "select count(*) from documents"'`.
- `make stack-clean` stops the stack and deletes its volumes, including the database.

## App on the host

To work on the API or the worker with reload, run them on the host against the stack's Postgres.
Start only the database, apply migrations, then run each process in its own terminal:

```bash
make stack-up-db
make db-migrate
make app-api
make app-worker
```

The full stack also serves the API on port 8000, so stop it with `make stack-down` first.

`make app-api` serves `http://127.0.0.1:8000`. `make app-worker` drains the job queue and moves
documents from `REGISTERED` to `READY`; set `DOC_FORGE_WORKER_POLL_SECONDS=0.1` for faster
polling. Both read `DATABASE_URL` and `DOC_FORGE_ARTIFACT_ROOT` from `.env`, and both use
deterministic answers unless `.env` selects another backend.

- `http://127.0.0.1:8000/docs` serves the Swagger UI only when `DOC_FORGE_ENABLE_SWAGGER=true`.
  `DOC_FORGE_ENVIRONMENT=dev` alone doesn't enable it.
- `http://127.0.0.1:8000/openapi.json` serves the schema on the same condition. It includes
  draft, diagnostic, and internal routes, so use [`api-contracts.md`](./api-contracts.md) for the
  intended external HTTP boundary.
- `POST /retrieval/query` is a local retrieval debug route and isn't part of the draft public
  contract.
- `POST /internal/run-next-job` exists for tests and local debugging. Use the worker for normal
  runs.

## Database migrations

```bash
make db-migrate
make db-revision MESSAGE='add lifecycle index'
```

`make db-migrate` applies migrations to `DATABASE_URL`. `make db-revision` writes a new revision
under `src/doc_forge/persistence/migrations/versions/`. A schema change to lifecycle metadata
updates both the SQLAlchemy table definitions and a reviewed Alembic revision.

## Observability and query context

```bash
make observability-up
make query-context-collect QUERY_ID=qry-123
make query-context-show QUERY_ID=qry-123
make observability-scan
make observability-down
```

- `make observability-up` builds and starts Postgres, Loki, Vector, and Grafana from
  `docker-compose.observability.yml`. Grafana is on `http://127.0.0.1:3000`.
  `observability-status` and `observability-logs` work like their `stack-` versions.
- `make query-context-collect` collects one query's bundle under
  `data/context/queries/<query_id>/`. `make query-context-show` prints the bundle's summary,
  citations, trace, replay, log, and eval paths.
- `make observability-scan` indexes the collected bundles into the observability Postgres.

## Cleanup

```bash
make clean-preview
make clean
```

`make clean-preview` lists the generated caches, lifecycle artifacts, query bundles, archived
logs, the uv cache in `./.tmp_uv_cache`, and tool virtual environments under `tools/` that
`make clean` would remove. `make clean` keeps files placed directly under `data/` and
non-generated files under `tools/`. Add `ARGS='--include-model-cache'` to also remove
`data/huggingface/`.

## Docs workstreams

```bash
make docs-workstream-new TYPE=feature SLUG=my-feature
```

Pick the type from `docs/harness/taxonomy/workstream-taxonomy.md`. The command creates the folder
under `docs/workstreams/` from the templates in `docs/harness/templates/`.

## PDF-to-Markdown conversion

Use this workflow for a one-off, high-fidelity Markdown copy of a text-based PDF when the
runtime `pypdf` extractor isn't good enough for reading, corpus preparation, or converter
evaluation. It runs locally and doesn't change the `doc_forge` ingestion backend.

A request looks like "Convert /absolute/path/to/source.pdf to Markdown." When an agent gets
that request, it starts and supervises the conversion itself:

1. Inspect the source with `pdfinfo` and render representative pages.
2. Write to a sibling directory named after the PDF stem, unless the user names another output
   location. If the directory exists, inspect it and don't overwrite earlier work without asking.
3. Keep restricted documents local. Don't upload the source to a hosted OCR or LLM service.
4. Run Marker with its local `llama.cpp` OCR backend. Marker starts and stops `llama-server`
   itself. If `llama-server` isn't installed, ask before installing `llama.cpp`.
5. Keep extracted images and page boundaries.
6. Change Marker's zero-based page separators into one-based markers such as
   `<!-- PDF page 1 -->`.
7. Run the checks under "Required validation" below.
8. Repair conversion loss only against the rendered source page, then hand off the Markdown file,
   the images, and `_meta.json`.

The conversion can take many minutes on a long or badly encoded PDF. Keep it attached, report
progress, and validate the result. Don't switch to a lower-quality converter because OCR is slow.

[Marker](https://github.com/datalab-to/marker) downloads model weights, but the command below
doesn't send the source PDF to a hosted service.

### Tool selection

A file-specific comparison on 2026-07-25 used `marker-pdf==2.0.0` and
`llama.cpp` build `10090` on a scholarly course reader with a table of contents,
margin notes, footnotes, formulas, code listings, and diagrams:

- Marker in `fast` mode with local OCR produced the best starting Markdown. It
  repaired broken custom-font ligatures, recovered reading order, grouped
  diagrams, removed repeated headers, and could emit page boundaries.
- Docling's standard pipeline recovered reading order and diagrams well, but
  left split ligatures such as `di ff erent` in this file.
- PyMuPDF4LLM was fast and lightweight, but its output for this file malformed
  the table of contents, omitted words, and split diagrams into multiple image
  fragments.

These observations are evidence for this document family, not a universal
converter ranking. Re-run a representative-page comparison before standardizing
on a converter for a materially different corpus.

Marker's code and model weights have different license terms. Before promoting
this operator workflow into the product runtime, review the current upstream
terms and the architecture guardrail in
[`architecture.md`](./architecture.md).

### Local setup and conversion

Marker's OCR backend needs `llama-server` from
[`llama.cpp`](https://github.com/ggml-org/llama.cpp). On macOS:

```bash
brew install llama.cpp
llama-server --version
```

Run Marker through an isolated `uv` environment so it does not alter the
project dependency graph:

```bash
export SOURCE_PDF="/absolute/path/to/source.pdf"
export MARKDOWN_OUTPUT_DIR="/absolute/path/to/output"

uv run --isolated --no-project --python 3.12 --with marker-pdf==2.0.0 \
  marker_single "$SOURCE_PDF" \
  --mode fast \
  --output_format markdown \
  --output_dir "$MARKDOWN_OUTPUT_DIR" \
  --MarkdownRenderer_paginate_output
```

Marker creates a directory named after the PDF stem containing:

- one Markdown file
- extracted image files referenced with relative links
- one `_meta.json` conversion record

The paginated renderer writes zero-based raw separators such as
`{0}------------------------------------------------`. For a human-facing
derivative, normalize them to explicit one-based markers such as
`<!-- PDF page 1 -->` without dropping or reordering any page.

### Required validation

Treat converter output as a draft. At minimum:

1. Compare the source page count with the number and sequence of Markdown page
   markers.
2. Check that every relative Markdown image reference resolves to an extracted
   file and that no empty `![]()` image tokens remain.
3. Search for replacement characters and custom-font artifacts such as
   `di!erent`, `e!ective`, `su"cient`, or split ligatures.
4. Inspect the first, middle, and last pages for reading order and heading
   hierarchy.
5. Render and compare pages containing tables, formulas, diagrams, margin
   notes, and code. OCR can repair prose while still truncating or flattening a
   code listing.
6. Repair only against the rendered source page, then repeat the structural
   checks.

Useful inspection commands:

```bash
pdfinfo "$SOURCE_PDF"
pdftoppm -f 1 -l 1 -png -r 140 "$SOURCE_PDF" /tmp/pdf-page
rg -n '!\[\]\(\)|�|[[:alpha:]]![[:alpha:]]' /absolute/path/to/output.md
rg -c '^<!-- PDF page [0-9]+ -->$' /absolute/path/to/output.md
```

Do not infer that a successful operator conversion adds scanned-PDF OCR, image
understanding, or rich layout reconstruction to the MVP. The product boundary
in [`mvp.md`](./mvp.md) remains authoritative.

## Tracing and context
- `logs` are stream-oriented container events archived under `data/logs/`; use them to inspect request, worker, and review activity around a query.
- `trace` is the durable per-query stage record persisted in `query_stage_traces` and exposed through `/queries/{query_id}/trace`.
- `replay` is the frozen query input bundle reconstructed from persisted state; query context collection writes it to `data/context/queries/<query_id>/replay.json`.
- Query-centric bundles under `data/context/queries/<query_id>/` index those assets together with `manifest.json`, filtered `logs/query-events.jsonl`, and any available eval metadata.
- The central observability stack ingests those filesystem outputs rather than replacing them:
  - Postgres indexes query/eval bundle metadata
  - Loki centralizes JSON service logs
  - Grafana provides the common UI

## Configuration
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
- `DOC_FORGE_UID` and `DOC_FORGE_GID` set the user that the Compose services run as, so they can write to `./data`. Make sets them to your user and group IDs.
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
- If imports fail, run `make setup-sync`.
- If optional model-backed embeddings or Apple Silicon generation fail to import, run `make setup-llm` or `make setup-mac`. Both check that the groups import.
- If Apple Silicon Docker runs stay deterministic, confirm host Ollama is reachable at `http://127.0.0.1:11434/api/tags`; `make stack-up` and `make e2e-test` only switch to Ollama when that health check succeeds.
- If you want Docker-backed local runs to use the Compose Ollama container instead of host Ollama, start with `COMPOSE_PROFILES=ollama DOC_FORGE_ANSWER_GENERATOR_BACKEND=ollama OLLAMA_BASE_URL=http://ollama:11434 make stack-up`.
- If you want to verify GPU-backed local generation on Apple Silicon, run one query after `make stack-up`, confirm `ollama ps` shows `llama3.2:1b` on `100% GPU`, and confirm archived API logs contain `event=\"llm generated\"` with `generator_backend=\"ollama\"`.
- If validation disagrees across environments, re-run the standard `fmt-check`, `lint`, `type`, `test`, and `verify` targets. Use `fmt` only when you want to apply automatic fixes.
- If Alembic commands fail immediately, verify that `DATABASE_URL` is set and points at a reachable database.
- If you encounter database authentication errors when connecting local processes to the Docker stack, run `make stack-clean` to delete the stale database volume and reset the credentials, then `make stack-up`. This deletes the local database.
- If the internal lifecycle app or worker fails at startup, verify `DATABASE_URL`, `DOC_FORGE_ARTIFACT_ROOT`, and migrations first.
- If the Docker stack can't write artifacts, check that `DOC_FORGE_UID` and `DOC_FORGE_GID` in `.env` don't override your user, then remove stale root-owned files under `./data`.
- If archived container logs are missing, verify that `data/logs/` is writable and that the container run mounted `/logs` successfully.
- If a query bundle is incomplete, inspect `data/context/queries/<query_id>/manifest.json`; missing components are listed explicitly under `missing_assets`.
- If the observability stack shows no runs, start with `make observability-scan` and confirm `data/context/queries/` contains collected bundles.
- If Grafana starts but shows no logs, confirm Vector has access to `data/logs/` and that Loki is reachable at `http://127.0.0.1:${OBSERVABILITY_LOKI_PORT:-3100}`.
- If a doc describes ingestion, parsing, or grounded answering as already implemented, reconcile it with `docs/evergreen/architecture.md` and the actual code before treating it as current behavior.

## Escalation / Ownership
- Durable repo and product truth belongs in `docs/evergreen/`.
- Time-scoped investigation and implementation planning can live under `docs/workstreams/`.
- Long-lived cross-cutting decisions belong in `docs/adrs/`.
- Repo-specific templates and playbooks live in `docs/harness/`.
