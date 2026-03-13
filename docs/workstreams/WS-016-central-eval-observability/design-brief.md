# Central Eval Observability Design Brief

## Summary
Implement a separate Docker Compose subsystem that centrally indexes query/eval
run metadata into Postgres and streams JSON service logs into Loki, while
keeping raw query bundles and full JSON artifacts on disk.

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

## Functional design
### 1. Metadata indexing
- `evalops-loader` scans `data/context/queries/` recursively.
- Each bundle directory is keyed by `query_id`.
- The loader reads `manifest.json` first and treats it as the required source of
  truth for bundle-level indexing.
- If present, the loader additionally reads:
  - `query-response.json`
  - `eval-result.json`
  - `execution-metadata.json`
- The loader writes normalized rows into Postgres.
- The loader is idempotent.
  - repeated scans update existing rows by `query_id`
  - absent optional files do not delete raw files on disk

### 2. Log shipping
- `vector` tails repo-local JSONL archives under:
  - `data/logs/compose/runs/**`
  - `data/logs/e2e/runs/**`
- Vector parses one JSON object per line and forwards the event to Loki.
- Required Loki labels:
  - `service`
  - `environment`
- Recommended labels when present in the payload:
  - `query_id`
  - `workspace_id`
  - `doc_id`
  - `run_id`
  - `test_id`
  - `case_id`
  - `source_kind`
- The raw JSON event body remains queryable in Loki.
- Do not make bundle-level `logs/query-events.jsonl` the primary source in v1.
  It may be ingested later as a secondary stream if needed.

### 3. Operator access pattern
- Query-centric flow:
  - search Postgres-backed metadata by `query_id`
  - inspect `workspace_id`, `support_state`, `answer_mode`, `source_kind`,
    `run_id`, and asset presence
  - pivot into Loki with `query_id` plus `service`
- Eval-centric flow:
  - search Postgres-backed metadata by `case_id` or `evaluator_outcome`
  - inspect trust outcome and criterion verdicts
  - pivot into the linked `query_id` and matching logs
- Disk-backed deep dive remains available:
  - use stored bundle root and asset paths to reopen raw artifacts outside the
    central subsystem

## Service responsibilities
- `telemetry-postgres`
  - relational metadata store only
  - no raw JSONL log ingestion
- `loki`
  - append-only log stream store
  - no bundle metadata modeling
- `grafana`
  - dashboards and explore UI
  - one Postgres datasource and one Loki datasource
- `vector`
  - file tailing, JSON parsing, label shaping, delivery to Loki
- `evalops-loader`
  - metadata scan, normalization, and upsert into Postgres

## Implementation requirements
- No changes to the app’s stable HTTP routes.
- No new writes from the app into this subsystem in v1.
- No Docker socket scraping as the primary log source.
- No attempt to centralize raw trace/replay/citation JSON documents into
  Postgres.
- Compose stack must mount the repo’s `data/` directory read-only where
  possible.

## Delivery sequence
1. Add the ADR for the storage split and ingest direction.
2. Add `docker-compose.observability.yml` and config files for Loki, Vector, and
   Grafana provisioning.
3. Implement `evalops-loader` as a small internal Python service or CLI runner.
4. Add a schema bootstrap/migration path for `telemetry-postgres`.
5. Add one sample dashboard or a minimal Grafana data source provisioning path.
6. Validate against at least one real eval bundle and one non-eval query bundle.

## Acceptance criteria
- The separate agent can implement the stack without choosing different
  databases or an alternate ingest model.
- Postgres stores searchable rows keyed by `query_id`, `case_id`, `run_id`,
  `test_id`, and `workspace_id`.
- Loki receives JSON service logs from existing repo-local archives.
- Grafana can show metadata and logs for at least one real query run end to end.

## Verified runtime state
- The stack has now been brought up successfully with:
  - `docker compose -f docker-compose.observability.yml up -d`
- Required bring-up fixes that were discovered during live verification:
  - `evalops-loader` must receive `--context-root` before the `scan`
    subcommand in the Compose command array.
  - `vector` must have a writable `data_dir` volume mounted.
  - `vector` VRL must avoid fallible `merge` usage and unsupported dynamic
    array indexing; regex extraction works for `run_id` and `test_id`.
- Verified outcomes against live local data:
  - Postgres indexed the current bundle set from `data/context/queries/`
  - Loki served streams parsed from `data/logs/**/*.jsonl`
  - Grafana health checks passed for both provisioned datasources
  - the provisioned `Central Eval Observability` dashboard was discoverable via
    the Grafana API
  - one known query id,
    `qry-b95ecf0a9e7a4f59a2aab81e75940505`, was confirmed across:
    - Postgres metadata
    - linked raw log source paths
    - Loki log streams with matching labels

## Remaining runtime gap
- `vector` still logs duplicate-fingerprint warnings for some e2e archive
  files with identical contents. The data path works, but archive hygiene or
  collector filtering still needs improvement.
