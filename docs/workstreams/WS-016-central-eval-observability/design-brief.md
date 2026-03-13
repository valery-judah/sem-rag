# Central Eval Observability Design Brief

## Summary
Implement a separate Docker Compose subsystem that ingests existing
filesystem-emitted query bundles and JSONL service logs, then writes central
copies into Postgres and Loki without adding synchronous app-side writes or new
stable HTTP APIs.

## System shape
- New stack entrypoint:
  - `docker compose -f docker-compose.observability.yml up`
- Services:
  - `telemetry-postgres`
  - `loki`
  - `grafana`
  - `vector`
  - `evalops-loader`
- Source data:
  - `data/logs/**/*.jsonl`
  - `data/context/queries/*/manifest.json`
  - optional bundle enrichments:
    - `query-response.json`
    - `eval-result.json`
    - `execution-metadata.json`
  - v2 full bundle documents:
    - `summary.json`
    - `trace.json`
    - `citations.json`
    - `replay.json`

## Functional design
### 1. Collection edge and ownership
- Filesystem outputs remain the canonical emission layer from the app.
- The app does not dual-write directly into Postgres on the request path.
- Centralization happens downstream:
  - `vector` ingests JSONL log files and writes central log copies
  - `evalops-loader` ingests query bundle files and writes normalized metadata
    plus v2 JSONB document copies

### 2. Postgres responsibilities
- `telemetry-postgres` is the primary central persistence layer for:
  - query/eval run metadata
  - parsed service log events
  - log ingest checkpoints
  - bundle asset indexes
  - v2 full bundle JSON documents
- Postgres remains the first store for both structured metadata and document
  retrieval in this local-first subsystem because it already supports:
  - `jsonb`
  - GIN indexes for JSONB queries
  - declarative partitioning
  - direct Grafana datasource integration

### 3. Log ingestion
- `vector` tails repo-local JSONL archives under:
  - `data/logs/compose/runs/**`
  - `data/logs/e2e/runs/**`
- Each log line is parsed as one JSON object.
- `vector` writes the same parsed event to two destinations:
  - Loki for stream exploration
  - Postgres `service_log_events` for durable relational correlation
- `vector` also maintains file-ingest progress in `log_ingest_files`.
- Log ingestion must be idempotent:
  - re-reading the same file must not duplicate logical events
  - event identity is derived from stable source coordinates and content hash

### 4. Bundle ingestion
- `evalops-loader` scans `data/context/queries/` recursively.
- The loader treats `manifest.json` as the required root document for each
  bundle.
- The loader upserts normalized rows into:
  - `query_context_runs`
  - `query_context_assets`
  - `eval_case_results`
- In v2, the loader additionally inserts full JSON documents into
  `bundle_documents`.
- Bundle ingestion must be idempotent:
  - `query_context_runs` upserts by `query_id`
  - `query_context_assets` upserts by `(query_id, asset_kind)`
  - `eval_case_results` upserts by `(query_id, case_id)`
  - `bundle_documents` deduplicates by `(query_id, document_kind, content_sha256)`

### 5. Loki policy
- Loki remains an operator-facing stream store, not the only retained log
  destination.
- Standard Loki labels are limited to low-cardinality fields:
  - `service`
  - `environment`
  - `source_family`
  - optional `source_kind`
  - optional `log_type`
- The following identifiers must not be promoted to normal Loki labels:
  - `query_id`
  - `workspace_id`
  - `doc_id`
  - `run_id`
  - `test_id`
  - `case_id`
- When needed in Loki, those identifiers travel as structured metadata rather
  than indexed labels.

### 6. Operator access pattern
- Query-centric flow:
  - search Postgres metadata by `query_id`
  - inspect `workspace_id`, `support_state`, `answer_mode`,
    `evaluator_outcome`, bundle assets, and any stored bundle documents
  - pivot to:
    - Postgres-backed `service_log_events`
    - Loki stream exploration for the same time range and service
- Eval-centric flow:
  - search Postgres metadata by `case_id`, `run_id`, `test_id`, or trust result
  - inspect verdicts and linked query bundle metadata
  - pivot to related Postgres log rows or Loki streams
- Document-centric v2 flow:
  - retrieve `trace`, `replay`, `citations`, and related bundle documents by
    `query_id`, `run_id`, or `case_id` from Postgres JSONB tables

## Service responsibilities
- `telemetry-postgres`
  - central store for metadata, parsed log events, ingest checkpoints, and v2
    bundle documents
- `loki`
  - append-only log exploration surface
  - no high-cardinality identifier indexing as standard labels
- `grafana`
  - one Postgres datasource and one Loki datasource
  - dashboards focus on finding a run in Postgres first, then pivoting
- `vector`
  - file tailing, JSON parsing, low-cardinality label shaping, structured
    metadata attachment, and delivery to Loki plus Postgres
- `evalops-loader`
  - metadata scan, normalization, upsert into Postgres, and v2 bundle document
    ingestion

## Implementation requirements
- No changes to the app’s stable HTTP routes.
- No request-path writes from `api` or `worker` into the central subsystem.
- No Docker socket scraping as the primary log source.
- No Promtail.
- Compose stack should mount the repo `data/` directory read-only where
  possible.
- The implementation must refactor the current subsystem toward the chosen
  design instead of preserving the older Loki-only log retention model.

## Delivery sequence
1. Update the ADR and WS-016 packet to freeze the corrected storage split.
2. Refactor the observability schema toward Postgres-backed log persistence.
3. Update Vector config to write parsed log events into Postgres and Loki while
   keeping Loki labels low-cardinality.
4. Update the loader to keep metadata upserts and add v2 document ingestion.
5. Validate against at least one real eval bundle and one non-eval query bundle.
6. Promote the design into evergreen docs only after the revised subsystem is
   implemented and exercised.

## Acceptance criteria
- The implementation agent can build the subsystem without choosing a different
  primary database or a different collector model.
- Postgres stores searchable rows keyed by `query_id`, `case_id`, `run_id`,
  `test_id`, `workspace_id`, and `service`.
- Postgres stores durable parsed service log rows, not just metadata about log
  source files.
- Loki receives the same parsed service log stream for tailing and exploration.
- Grafana can support a run-first workflow that begins in Postgres and pivots to
  Postgres-backed log rows or Loki.
- V2 stores at least one full bundle’s `trace`, `replay`, and `citations`
  documents in Postgres JSONB and retrieves them by correlation keys.

## Notes
- Promtail is not the recommended collector path for this design because it is
  deprecated and has reached end of life.
- Loki label design must follow low-cardinality guidance; correlation
  identifiers belong in Postgres and optionally in Loki structured metadata.
