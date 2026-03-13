# Agent Context: Central Eval Observability

## Goal
Implement a separate local observability stack that centrally indexes existing
query/eval bundle metadata and streams existing JSON service logs, without
changing the main app contract.

## Read in this order
1. [`/Users/val/projects/rag/sem-rag/docs/evergreen/architecture.md`](/Users/val/projects/rag/sem-rag/docs/evergreen/architecture.md)
2. [`/Users/val/projects/rag/sem-rag/docs/evergreen/runbook.md`](/Users/val/projects/rag/sem-rag/docs/evergreen/runbook.md)
3. [`/Users/val/projects/rag/sem-rag/docs/workstreams/WS-014-logs/workstream.md`](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-014-logs/workstream.md)
4. [`/Users/val/projects/rag/sem-rag/docs/workstreams/WS-015-context-collecting/workstream.md`](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-015-context-collecting/workstream.md)
5. [`/Users/val/projects/rag/sem-rag/src/doc_forge/app/logging.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/app/logging.py)
6. [`/Users/val/projects/rag/sem-rag/src/doc_forge/query/context_archive.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/query/context_archive.py)
7. [`/Users/val/projects/rag/sem-rag/src/doc_forge/evaluation/answer_layer.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/evaluation/answer_layer.py)
8. [`/Users/val/projects/rag/sem-rag/e2e/eval_support.py`](/Users/val/projects/rag/sem-rag/e2e/eval_support.py)
9. [`/Users/val/projects/rag/sem-rag/docker-compose.yml`](/Users/val/projects/rag/sem-rag/docker-compose.yml)

## What already exists
- JSON service logs are written to repo-local files under `data/logs/`.
- Query-centric context bundles are written under `data/context/queries/<query_id>/`.
- Query manifests already include the main correlation keys:
  - `query_id`
  - `workspace_id`
  - `case_id`
  - `test_id`
  - `run_id`
  - `source_kind`
  - `support_state`
  - `answer_mode`
  - `evaluator_outcome`
- Eval executions already write:
  - `eval-result.json`
  - `execution-metadata.json`
- Non-eval bundles may still include `query-response.json`.

## Data shapes to respect
### JSON logs
- One JSON event per line.
- Stable top-level fields already present:
  - `ts`
  - `event`
  - `service`
  - `environment`
- Many events also carry domain ids such as:
  - `query_id`
  - `workspace_id`
  - `doc_id`

### Query bundle manifest
- The manifest is the required root document for central metadata indexing.
- Optional companion files may enrich the metadata model:
  - `query-response.json`
  - `eval-result.json`
  - `execution-metadata.json`

## Required implementation outcome
- Add a separate Compose stack:
  - `docker-compose.observability.yml`
- Add a metadata store:
  - Postgres
- Add a log store:
  - Loki
- Add a common UI:
  - Grafana
- Add a log collector:
  - Vector
- Add a metadata ingester:
  - `evalops-loader`

## Hard constraints
- No stable HTTP API changes.
- No app-side distributed tracing backend.
- No replacement of repo-local JSON logs or query bundles.
- The central subsystem must ingest from filesystem outputs in v1.
- Do not use Docker socket scraping as the primary log ingest path.
- Do not ingest full trace/replay/citation payload bodies into Postgres in v1.

## Required correlation model
- First-class keys:
  - `query_id`
  - `case_id`
  - `run_id`
  - `test_id`
  - `workspace_id`
  - `service`
- Primary user flows:
  - query-centric: find run metadata first, then logs
  - eval-centric: find case/result first, then linked query run and logs

## Deliverables expected from the implementation agent
- `docker-compose.observability.yml`
- service configs for Loki, Vector, and Grafana provisioning
- metadata schema/bootstrap for telemetry Postgres
- a loader implementation that upserts existing query bundles
- validation or smoke coverage proving one eval and one non-eval bundle ingest
- runbook additions only after the subsystem is working

## Out of scope
- Production deployment
- retention tuning beyond local defaults
- metrics or tracing backends
- replacing the current filesystem-first debug path
