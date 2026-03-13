# Agent Context: Central Eval Observability

## Goal
Refactor the current observability subsystem toward a Postgres-centered design
that keeps filesystem outputs as the collection edge, writes central copies of
parsed service logs into Postgres and Loki, and stores v2 bundle documents in
Postgres JSONB without changing the main app contract.

## Read in this order
1. [architecture.md](/home/val/projects/sem-rag/docs/evergreen/architecture.md)
2. [runbook.md](/home/val/projects/sem-rag/docs/evergreen/runbook.md)
3. [WS-014 logs](/home/val/projects/sem-rag/docs/workstreams/WS-014-logs/workstream.md)
4. [WS-015 context collecting](/home/val/projects/sem-rag/docs/workstreams/WS-015-context-collecting/workstream.md)
5. [logging.py](/home/val/projects/sem-rag/src/doc_forge/app/logging.py)
6. [context_archive.py](/home/val/projects/sem-rag/src/doc_forge/query/context_archive.py)
7. [answer_layer.py](/home/val/projects/sem-rag/src/doc_forge/evaluation/answer_layer.py)
8. [eval_support.py](/home/val/projects/sem-rag/e2e/eval_support.py)
9. [docker-compose.yml](/home/val/projects/sem-rag/docker-compose.yml)

## Current repo baseline
- JSON service logs are already written to repo-local files under `data/logs/`.
- Query-centric context bundles are already written under
  `data/context/queries/<query_id>/`.
- The repo already contains an earlier central observability implementation that
  indexes bundle metadata into Postgres and ships logs to Loki.
- That baseline is not the target design for this workstream:
  - it does not treat Postgres as the central persistence layer for parsed log
    events
  - it overuses Loki labels for correlation identifiers
  - it does not centralize full bundle JSON documents in Postgres JSONB in v2

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
  - `run_id`
  - `test_id`
  - `case_id`

### Query bundle manifest
- `manifest.json` is the required root document for central metadata indexing.
- Manifests already expose:
  - `query_id`
  - `workspace_id`
  - `case_id`
  - `test_id`
  - `run_id`
  - `source_kind`
  - `support_state`
  - `answer_mode`
  - `evaluator_outcome`
- Optional companion files may enrich the metadata model:
  - `query-response.json`
  - `eval-result.json`
  - `execution-metadata.json`

### Full bundle documents for v2
- `summary.json`
- `trace.json`
- `citations.json`
- `replay.json`

## Required implementation outcome
- Keep a separate Compose stack:
  - `docker-compose.observability.yml`
- Keep the chosen services:
  - `telemetry-postgres`
  - `loki`
  - `grafana`
  - `vector`
  - `evalops-loader`
- Refactor responsibilities so that:
  - `vector` writes parsed log events to Loki and Postgres
  - `evalops-loader` writes normalized metadata to Postgres
  - `evalops-loader` writes full bundle JSON documents to Postgres in v2

## Hard constraints
- No stable HTTP API changes.
- No app-side distributed tracing backend.
- No replacement of repo-local JSON logs or query bundles.
- No request-path app-side dual write into Postgres.
- The central subsystem must ingest from filesystem outputs in v1.
- Do not use Docker socket scraping as the primary log ingest path.
- Do not use Promtail.
- Do not use `query_id`, `workspace_id`, `doc_id`, `run_id`, `test_id`, or
  `case_id` as standard Loki labels.

## Required correlation model
- First-class Postgres keys:
  - `query_id`
  - `case_id`
  - `run_id`
  - `test_id`
  - `workspace_id`
  - `service`
- Primary operator flows:
  - query-centric:
    - find run metadata in Postgres
    - pivot to Postgres-backed log rows or Loki
  - eval-centric:
    - find case or run result in Postgres
    - pivot to linked bundle metadata, documents, and logs
  - document-centric v2:
    - fetch `trace`, `replay`, and `citations` from Postgres by correlation key

## Deliverables expected from the implementation agent
- updated `docker-compose.observability.yml`
- updated service configs for Loki, Vector, and Grafana provisioning
- updated observability schema and migration/bootstrap path for Postgres-backed
  log persistence
- loader changes that keep metadata upserts and add v2 bundle document ingest
- validation or smoke coverage proving one eval and one non-eval bundle ingest
- evergreen doc updates only after the subsystem is working

## Out of scope
- production deployment
- a second analytics or document store in v1 or default v2
- metrics or tracing backends
- replacing the filesystem-first debug path
- inventing a new app API for the collector subsystem
