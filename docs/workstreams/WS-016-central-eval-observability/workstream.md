---
artifact_kind: workstream
id: WS-016
title: Central Eval Observability
work_type: feature
status: active
owner:
created: 2026-03-13
updated: 2026-03-13
---

# Summary
Design a separate Docker Compose subsystem that centrally collects eval-running
metadata, query-context bundle indexes, and JSON service logs from `api` and
`worker` without changing the stable app API or replacing the existing
filesystem-first debug flow.

## Objective
Define a v1 observability subsystem that gives operators and eval workflows one
central place to find query runs, eval case executions, and correlated service
logs by `query_id`, `case_id`, `run_id`, `test_id`, or `workspace_id`.

## Non-goals
- No stable HTTP API changes in the main app.
- No app-side distributed tracing or OpenTelemetry backend.
- No replacement of repo-local JSON log archives or query-context bundles.
- No ClickHouse or second analytics-first event store in v1.
- No ingestion of full trace, replay, or citation payload bodies into the
  central relational store in v1.

## Current status
- Implemented a separate Compose stack in `docker-compose.observability.yml`
  with:
  - `telemetry-postgres`
  - `loki`
  - `grafana`
  - `vector`
  - `evalops-loader`
- Added an internal metadata schema and loader under
  `src/doc_forge/observability/`.
- Added an operator CLI under `src/doc_forge/devtools/evalops_loader.py`.
- Added Grafana datasource and dashboard provisioning plus Loki and Vector
  configs under `observability/`.
- Added targeted loader and CLI tests.
- Repo-local JSON logs and query bundles remain the canonical emitted artifacts;
  the new subsystem ingests from them rather than replacing them.
- Verified the stack end to end against live repo data after fixing two
  orchestration defects:
  - `evalops-loader` was starting with `--context-root` after the `scan`
    subcommand, so `argparse` rejected the flag and the container restarted.
  - `vector` was missing its writable `data_dir` mount and had invalid VRL in
    `observability/vector/vector.yaml`, so the container restarted before any
    logs were shipped.
- After those fixes:
  - `telemetry-postgres` indexed `19` live query bundles into
    `query_context_runs`
  - `query_context_assets` contained `190` rows
  - `eval_case_results` contained `11` rows
  - `log_sources` contained `38` rows
  - `loki` served live streams from the archived JSON log files
  - `grafana` provisioned both datasources and the
    `Central Eval Observability` dashboard successfully

## Chosen stack
- `telemetry-postgres`
  - source of truth for structured eval/query run metadata and bundle indexes
- `loki`
  - source of truth for append-only JSON service logs
- `grafana`
  - common UI surface over Postgres and Loki
- `vector`
  - log collector that tails repo-local JSONL archives and ships to Loki
- `evalops-loader`
  - metadata ingester that scans `data/context/queries/` and writes normalized
    records into Postgres

## Why this split
- Logs and eval/query metadata have different access patterns.
  - JSON service logs are append-only streams and fit Loki.
  - Eval/query bundle metadata is relational, low volume, and filter-heavy, so
    Postgres is a better fit.
- The repo already emits stable filesystem artifacts.
  - v1 should ingest from those existing outputs instead of forcing the app to
    dual-write into a new central system.
- The dominant debug path is correlation-first.
  - operators usually start from `query_id`, `case_id`, `run_id`, `test_id`, or
    `workspace_id`, then pivot into logs and bundle assets.

## Next step
- Reduce noisy duplicate-fingerprint warnings in `vector`.
  The current archive shape includes some duplicated or renamed e2e log files,
  which does not block ingestion but does produce low-signal runtime noise.
- Add a durable smoke validation for
  `docker compose -f docker-compose.observability.yml up` so the live stack
  bring-up is covered outside ad hoc operator checks.
- Tighten dashboard and query ergonomics only where the current
  Postgres-to-Loki pivot still feels thin in practice.

## Relevant context
- paths:
  - `docs/evergreen/architecture.md`
  - `docs/evergreen/runbook.md`
  - `docs/workstreams/WS-014-logs/workstream.md`
  - `docs/workstreams/WS-015-context-collecting/workstream.md`
  - `src/doc_forge/app/logging.py`
  - `src/doc_forge/query/context_archive.py`
  - `src/doc_forge/evaluation/answer_layer.py`
  - `e2e/eval_support.py`
  - `docker-compose.yml`
- components:
  - repo-local JSONL log archives
  - query-context collector and bundle manifest
  - answer-layer eval outputs
  - e2e eval execution artifacts
- constraints:
  - keep repo-local logs and bundles as the primary emitted artifacts
  - central subsystem must run as a separate Compose stack
  - do not scrape the Docker socket as the primary source in v1
  - keep the main app contract unchanged
- read first:
  - `docs/workstreams/WS-016-central-eval-observability/design-brief.md`
  - `docs/workstreams/WS-016-central-eval-observability/agent-context.md`
  - `docs/workstreams/WS-016-central-eval-observability/schema-sketch.md`

## Workflow steps
1. Freeze the chosen storage split and ingest direction.
2. Implement the metadata schema, log label set, and service boundaries.
3. Validate the separate Compose stack against real existing bundles and log
   archives.
4. Stabilize runtime bring-up and reduce collector noise.

## Validation
- `uv run pytest tests/observability/test_loader.py tests/test_evalops_loader_cli.py -q`
- `uv run ruff check src/doc_forge/observability src/doc_forge/devtools/evalops_loader.py tests/observability/test_loader.py tests/test_evalops_loader_cli.py`
- `docker compose -f docker-compose.observability.yml up -d`
- live operator verification:
  - `telemetry-postgres`, `loki`, `grafana`, `vector`, and `evalops-loader`
    all reached a running state after the compose and Vector fixes
  - confirmed Postgres row counts:
    - `query_context_runs=19`
    - `query_context_assets=190`
    - `eval_case_results=11`
    - `log_sources=38`
  - confirmed Loki readiness and log ingestion from repo-local archives
  - confirmed Grafana health plus successful datasource connectivity for both
    Loki and Postgres
  - confirmed the provisioned dashboard is visible through the Grafana API
  - confirmed one real correlation path by `query_id`:
    `qry-b95ecf0a9e7a4f59a2aab81e75940505` existed in Postgres metadata and was
    also queryable in Loki with matching `service`, `run_id`, and
    `workspace_id`

## Known issues
- `vector` currently emits duplicate-fingerprint warnings for some archived e2e
  log files because the archive contains duplicate or renamed files with the
  same contents. This does not block ingestion, but it should be cleaned up or
  filtered so operator logs stay high-signal.

## Linked artifacts
- [`design-brief.md`](./design-brief.md)
- [`agent-context.md`](./agent-context.md)
- [`schema-sketch.md`](./schema-sketch.md)
- [`/Users/val/projects/rag/sem-rag/docs/adrs/ADR-central-eval-observability-store.md`](/Users/val/projects/rag/sem-rag/docs/adrs/ADR-central-eval-observability-store.md)
- [`/Users/val/projects/rag/sem-rag/docs/workstreams/WS-014-logs/workstream.md`](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-014-logs/workstream.md)
- [`/Users/val/projects/rag/sem-rag/docs/workstreams/WS-015-context-collecting/workstream.md`](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-015-context-collecting/workstream.md)
