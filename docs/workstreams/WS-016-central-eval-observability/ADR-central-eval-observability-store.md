# ADR: Central Eval Observability Store

- Status: proposed
- Date: 2026-03-13

## Context
The repo already emits two important filesystem-first observability surfaces:

- repo-local JSONL service logs under `data/logs/`
- query-centric context bundles under `data/context/queries/`

Those outputs are sufficient for manual debugging and local eval analysis, but
they are not enough for a central operator workflow on their own. The earlier
WS-016 design improved central visibility, but it still treated Loki as the
only retained log destination and promoted high-cardinality identifiers too
aggressively into Loki labels.

The subsystem we need should:

- stay local-first and Docker Compose based
- reuse existing filesystem outputs as ingest sources
- avoid stable API changes in the main app
- keep filesystem outputs as the collection edge
- write central copies of structured metadata and parsed log events into a
  database-backed store
- keep Loki useful for tailing and stream exploration without abusing its label
  model

## Decision
We will design the central eval observability subsystem around:

- Postgres for structured query/eval metadata
- Postgres for durable parsed service log events
- Postgres JSONB for v2 full bundle documents
- Loki for append-only log tailing and stream exploration
- Grafana as the common UI
- Vector as the collector
- a small loader service that indexes query bundles from the filesystem into
  Postgres

### Storage split
1. **Postgres**
   - central persistence layer for normalized query/eval metadata
   - central persistence layer for parsed JSON service log events
   - central persistence layer for bundle asset indexes and ingest checkpoints
   - v2 home for full bundle JSON documents through `jsonb`
   - keyed by `query_id`, `case_id`, `run_id`, `test_id`, `workspace_id`, and
     `service`

2. **Loki**
   - operator log surface for tailing and exploration
   - receives the same parsed service log stream as Postgres
   - uses only low-cardinality labels such as `service`, `environment`, and
     `source_family`
   - carries `query_id`, `run_id`, `test_id`, `case_id`, `workspace_id`, and
     `doc_id` as structured metadata when needed, not as standard labels

3. **Filesystem remains canonical for emitted artifacts**
   - raw `manifest.json`, `summary.json`, `trace.json`, `replay.json`,
     `citations.json`, `query-response.json`, `eval-result.json`, and
     `execution-metadata.json` remain the app-emitted collection edge
   - central storage is populated by collector and loader ingestion from those
     outputs rather than by request-path dual writes

### Ingest direction
- V1 ingest comes from existing filesystem outputs:
  - `data/logs/**/*.jsonl`
  - `data/context/queries/*/manifest.json`
  - optional bundle enrichments
- `vector` tails JSONL service logs, parses them, and writes central copies
  into:
  - Loki
  - Postgres `service_log_events`
- `evalops-loader` scans query bundles and writes:
  - `query_context_runs`
  - `query_context_assets`
  - `eval_case_results`
- In v2, `evalops-loader` also writes full bundle documents into
  `bundle_documents`.
- V1 does not use Docker socket scraping as the primary ingestion path.
- V1 does not require the main app to dual-write into the new subsystem.

## Consequences
- Positive:
  - keeps the app hot path unchanged while still centralizing observability data
  - gives operators one Postgres-first correlation surface for runs, evals, and
    parsed logs
  - keeps Loki available for the workflows it is good at
  - supports v2 bundle document retrieval without introducing a second store
- Positive:
  - Postgres already provides `jsonb`, GIN indexing, partitioning support, and
    a direct Grafana datasource, which keeps the local operator surface simple
- Tradeoff:
  - the subsystem still operates two central stores instead of one
- Tradeoff:
  - collector and loader idempotence must be engineered carefully
- Tradeoff:
  - a future second store may still be needed if payload size, retention, or
    query shape outgrow what is comfortable in Postgres

## Alternatives considered
- **Loki as the only central log store**
  - rejected because it is weaker for joins, relational correlation, retention
    control, and bundle-aware analysis
- **Single Postgres store with no Loki**
  - rejected because operators still benefit from a dedicated tail/explore log
    surface in Grafana Explore
- **Promtail as the collector**
  - rejected because Promtail is deprecated and has reached end of life, while
    Vector already fits the required file-tailing and multi-sink model
- **ClickHouse or another second store in v1**
  - rejected because local-first observability does not yet justify the extra
    operational and modeling weight
- **OTEL collector plus tracing backend**
  - rejected because the repo does not yet need distributed tracing and the
    existing filesystem outputs are already structured enough to ingest directly

## References
- Vector file source and collector docs: <https://vector.dev/docs/reference/configuration/sources/file/>
- Loki label-cardinality guidance:
  <https://grafana.com/docs/loki/latest/get-started/labels/cardinality/>
- Grafana PostgreSQL datasource docs:
  <https://grafana.com/docs/grafana/latest/datasources/postgres/>

## Related workstreams
- `docs/workstreams/WS-014-logs/`
- `docs/workstreams/WS-015-context-collecting/`
- `docs/workstreams/WS-016-central-eval-observability/`
