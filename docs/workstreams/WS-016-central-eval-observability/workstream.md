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
Supersede the earlier Loki-centric observability packet with a Postgres-centered
design that keeps filesystem outputs as the collection edge, centralizes parsed
service logs and structured query/eval metadata in Postgres, and keeps Loki as
the operator log-exploration surface.

## Objective
Define a decision-complete local observability subsystem that:

- ingests existing repo-local JSONL logs and query bundles without changing the
  stable app API
- writes central copies of parsed service log events into Postgres
- indexes query/eval bundle metadata in Postgres
- keeps Loki available for tailing, stream exploration, and Grafana Explore
- stores full bundle JSON documents in Postgres JSONB in v2 unless operational
  evidence later justifies a second store

## Non-goals
- No stable HTTP API changes in the main app.
- No app-side synchronous SQL writes on the request path.
- No replacement of repo-local JSON log archives or query bundles.
- No Promtail-based collector path.
- No high-cardinality Loki label set for correlation identifiers.
- No second analytics or document database unless Postgres proves insufficient.

## Current repo truth
- The repo already contains a separate Compose-based observability subsystem and
  a first-pass WS-016 packet.
- That earlier packet reflects an older design:
  - Postgres indexes bundle metadata.
  - Loki is treated as the only central log persistence target.
  - high-cardinality identifiers are described as Loki labels.
  - full bundle JSON documents are intentionally kept out of Postgres in v1.
- This workstream supersedes that earlier packet as the chosen target design.
- Evergreen docs remain responsible for implemented repo truth and should only
  be updated after the revised subsystem exists and is exercised.

## Chosen stack
- `telemetry-postgres`
  - primary central persistence layer for structured query/eval metadata,
    parsed service log events, bundle asset indexes, and v2 bundle documents
- `loki`
  - stream-oriented operator log surface for tailing and exploration
- `grafana`
  - common operator surface across Postgres and Loki
- `vector`
  - collector that tails repo-local JSONL archives, parses them, and writes
    central copies into Loki and Postgres
- `evalops-loader`
  - bundle ingester that scans `data/context/queries/`, upserts normalized
    metadata into Postgres, and ingests full bundle JSON documents in v2

## Why this split
- Filesystem outputs already exist and are structured enough to serve as the
  collection edge.
- Query/eval correlation and document retrieval are relational-plus-document
  workloads and fit Postgres well enough for a local-first subsystem.
- Loki remains useful for stream browsing, but low-cardinality label guidance
  makes it the wrong primary store for correlation identifiers such as
  `query_id`, `run_id`, `test_id`, and `case_id`.
- The dominant operator flow should be:
  - find the run in Postgres
  - inspect metadata and linked assets or stored bundle documents
  - pivot to Postgres-backed log rows or Loki stream exploration as needed

## Next step
- Use the revised packet as the source of truth for refactoring the current
  observability subsystem.
- Implement Postgres-backed parsed log persistence, low-cardinality Loki
  labeling, and v2 Postgres JSONB bundle-document ingest.
- Update evergreen docs only after the revised subsystem is implemented and
  validated against real repo data.

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
  - repo-local JSONL log archives under `data/logs/`
  - query-centric bundles under `data/context/queries/`
  - existing observability Postgres schema and loader
  - existing Loki, Vector, and Grafana configs
- constraints:
  - keep filesystem artifacts as the canonical emission layer
  - central writes happen in the collector and loader subsystem, not in the app
  - keep the central subsystem startable as a separate Compose stack
  - do not promote high-cardinality ids into standard Loki labels

## Workflow steps
1. Freeze the corrected storage split and ingest direction.
2. Specify the Postgres schema groups for metadata, log events, and v2 bundle
   documents.
3. Specify the Loki label and structured-metadata policy.
4. Hand off the implementation packet for refactoring the current subsystem.

## Validation
- Docs-only change:
  - no mandatory command run
- Required review checks:
  - all WS-016 docs and the ADR agree on the chosen stack and ingest direction
  - no file claims the revised subsystem is already implemented
  - `query_id`, `run_id`, `test_id`, `case_id`, `workspace_id`, and `doc_id`
    are described as Postgres correlation keys, not standard Loki labels
  - v2 bundle document storage is described as Postgres JSONB unless evidence
    later justifies a second store

## Linked artifacts
- [design-brief.md](./design-brief.md)
- [agent-context.md](./agent-context.md)
- [schema-sketch.md](./schema-sketch.md)
- [ADR-central-eval-observability-store.md](/home/val/projects/sem-rag/docs/adrs/ADR-central-eval-observability-store.md)
- [WS-014 logs](/home/val/projects/sem-rag/docs/workstreams/WS-014-logs/workstream.md)
- [WS-015 context collecting](/home/val/projects/sem-rag/docs/workstreams/WS-015-context-collecting/workstream.md)
