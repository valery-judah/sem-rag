# ADR: Central Eval Observability Store

- Status: proposed
- Date: 2026-03-13

## Context
The repo already emits two important filesystem-first observability surfaces:

- repo-local JSONL service logs under `data/logs/`
- query-centric context bundles under `data/context/queries/`

These outputs are sufficient for manual debugging and for local eval analysis,
but they are not centrally searchable. Operators currently need to navigate the
filesystem directly, and there is no single place to filter runs by `query_id`,
`case_id`, `run_id`, `test_id`, or `workspace_id` and then pivot into service
logs.

The subsystem we need should:

- stay local-first and Docker Compose based
- reuse existing filesystem outputs as ingest sources
- avoid stable API changes in the main app
- keep raw payloads on disk rather than duplicating every JSON artifact into a
  central database

## Decision
We will design the v1 central eval observability subsystem around:

- Postgres for structured query/eval metadata
- Loki for append-only JSON service logs
- Grafana as the common UI
- Vector as the log collector
- a small loader service that indexes query bundles from the filesystem into
  Postgres

### Storage split
1. **Postgres**
   - source of truth for normalized query/eval run metadata
   - indexes bundle-level facts and selected eval verdicts
   - keyed by `query_id`, `case_id`, `run_id`, `test_id`, and `workspace_id`

2. **Loki**
   - source of truth for centralized service log browsing
   - ingests existing JSONL logs from the filesystem
   - uses labels for `service`, `environment`, and correlation ids when present

3. **Filesystem remains canonical for raw artifacts**
   - raw `manifest.json`, `trace.json`, `replay.json`, `citations.json`,
     `query-response.json`, `eval-result.json`, and `execution-metadata.json`
     remain on disk
   - Postgres stores references and summary fields, not full denormalized copies

### Ingest direction
- V1 ingest comes from existing filesystem outputs:
  - `data/logs/**/*.jsonl`
  - `data/context/queries/*/manifest.json`
  - optional bundle enrichments
- V1 does not use Docker socket scraping as the primary ingestion path.
- V1 does not require the main app to dual-write into the new subsystem.

## Consequences
- Positive:
  - reuses stable existing outputs
  - low-risk integration with the current app
  - clean separation between stream logs and relational run metadata
  - easy operator path from run metadata to logs in Grafana
- Positive:
  - local retention of raw artifacts stays simple and audit-friendly
- Tradeoff:
  - two stores must be operated instead of one
- Tradeoff:
  - raw trace/replay/citation payloads are not centrally queryable in SQL in v1
- Tradeoff:
  - central views depend on loader freshness and filesystem availability

## Alternatives considered
- **Single Postgres store for both logs and metadata**
  - rejected for v1 because append-only JSON log browsing and label-style log
    filtering are a weaker fit than Loki
- **ClickHouse for both logs and eval metadata**
  - rejected for v1 because it adds more operational and modeling weight than we
    need for local-first centralization
- **OTEL collector plus tracing backend**
  - rejected for v1 because the repo does not yet need distributed tracing and
    the current outputs are already structured enough to ingest directly

## Related workstreams
- `docs/workstreams/WS-014-logs/`
- `docs/workstreams/WS-015-context-collecting/`
- `docs/workstreams/WS-016-central-eval-observability/`
