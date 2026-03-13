# Schema Sketch: Central Eval Observability

## Summary
This document sketches the Postgres schema groups, idempotent ingest keys, and
Loki indexing policy for the Postgres-centered central observability subsystem.

## Postgres tables
### `query_context_runs`
- one row per collected query bundle
- primary key:
  - `query_id`
- columns:
  - `query_id text not null`
  - `workspace_id text null`
  - `question text null`
  - `submitted_at timestamptz null`
  - `completed_at timestamptz null`
  - `collected_at timestamptz not null`
  - `source_kind text not null`
  - `run_id text null`
  - `test_id text null`
  - `case_id text null`
  - `support_state text null`
  - `answer_mode text null`
  - `evaluator_outcome text null`
  - `bundle_root text not null`
  - `environment text null`
- indexes:
  - `(workspace_id)`
  - `(run_id)`
  - `(test_id)`
  - `(case_id)`
  - `(source_kind, collected_at desc)`

### `query_context_assets`
- one row per indexed bundle asset path
- keys:
  - foreign key to `query_context_runs(query_id)`
  - unique `(query_id, asset_kind)`
- columns:
  - `query_id text not null`
  - `asset_kind text not null`
  - `relative_path text null`
  - `present boolean not null`
  - `missing_reason text null`

### `eval_case_results`
- one row per eval-scored case/run
- keys:
  - foreign key to `query_context_runs(query_id)`
  - unique `(query_id, case_id)`
- columns:
  - `query_id text not null`
  - `case_id text not null`
  - `workspace_id text null`
  - `run_id text null`
  - `test_id text null`
  - `trust_outcome text not null`
  - `support_alignment_verdict text null`
  - `scope_control_verdict text null`
  - `provenance_quality_verdict text null`
  - `abstention_behavior_verdict text null`
  - `overall_trust_verdict text null`
- indexes:
  - `(case_id, trust_outcome)`
  - `(trust_outcome)`

### `service_log_events`
- one row per parsed JSON log event
- primary key:
  - `event_id`
- columns:
  - `event_id text not null`
  - `ts timestamptz not null`
  - `ingested_at timestamptz not null`
  - `service text not null`
  - `environment text null`
  - `level text null`
  - `event text not null`
  - `query_id text null`
  - `workspace_id text null`
  - `doc_id text null`
  - `run_id text null`
  - `test_id text null`
  - `case_id text null`
  - `source_kind text null`
  - `source_path text not null`
  - `line_number integer not null`
  - `payload jsonb not null`
- idempotent ingest key:
  - `event_id = sha256(source_path + ":" + line_number + ":" + raw_line_sha256)`
- indexes:
  - `(service, ts desc)`
  - `(ts desc)`
  - `(query_id, ts desc)`
  - `(run_id, ts desc)`
  - `(case_id, ts desc)`
  - `(workspace_id, ts desc)`
  - `(event, ts desc)`
- partition guidance:
  - partition by day or week on `ts`

### `log_ingest_files`
- one row per tailed source file and collector checkpoint
- primary key:
  - `(source_path, service)`
- columns:
  - `source_path text not null`
  - `service text not null`
  - `bytes_seen bigint not null`
  - `lines_seen bigint not null`
  - `last_event_ts timestamptz null`
  - `last_ingested_at timestamptz not null`
- purpose:
  - checkpoint collector progress
  - support resumable ingest and operator inspection

### `bundle_documents`
- v2 table for full bundle JSON documents
- primary key:
  - `document_id`
- columns:
  - `document_id text not null`
  - `query_id text not null`
  - `workspace_id text null`
  - `run_id text null`
  - `test_id text null`
  - `case_id text null`
  - `document_kind text not null`
  - `captured_at timestamptz null`
  - `source_path text not null`
  - `content_sha256 text not null`
  - `payload jsonb not null`
  - `payload_bytes bigint not null`
- dedupe key:
  - unique `(query_id, document_kind, content_sha256)`
- indexes:
  - `(query_id, document_kind)`
  - `(run_id, document_kind)`
  - `(case_id, document_kind)`
  - GIN on `payload`
- partition guidance:
  - partition by month if document volume or retention warrants it

### `bundle_document_links`
- optional helper table when explicit parent-child relationships are useful
- example columns:
  - `parent_document_id`
  - `child_document_id`
  - `link_kind`

## Asset kinds
- `summary`
- `citations`
- `trace`
- `replay`
- `query_response`
- `eval_result`
- `execution_metadata`
- `query_events`
- `api_log`
- `worker_log`

## Loki policy
### Required labels
- `service`
- `environment`
- `source_family`

### Optional low-cardinality labels
- `source_kind`
- `log_type`

### Structured metadata
- `query_id`
- `workspace_id`
- `doc_id`
- `run_id`
- `test_id`
- `case_id`

### Do not use as standard labels
- `query_id`
- `workspace_id`
- `doc_id`
- `run_id`
- `test_id`
- `case_id`

## Example Postgres rows
### `query_context_runs`
```json
{
  "query_id": "qry-10f4415b6be249f7a96b06a94d68ed6b",
  "workspace_id": "ws-eval-lookup_rn1_001",
  "question": "What latency target defined acceptable end-to-end performance for the study?",
  "submitted_at": "2026-03-13T04:08:57.440858Z",
  "completed_at": "2026-03-13T04:08:57.452898Z",
  "collected_at": "2026-03-13T04:08:57.509218Z",
  "source_kind": "eval",
  "run_id": "573ba010b63d4ac5b3d61d0deb1a2921",
  "test_id": "e2e/test_eval_answer_layer_smoke.py::test_authored_answer_layer_smoke_cases_execute_over_real_stack[lookup_rn1_001]",
  "case_id": "lookup_rn1_001",
  "support_state": "insufficient",
  "answer_mode": "full_abstention",
  "evaluator_outcome": "not_trustworthy",
  "bundle_root": "data/context/queries/qry-10f4415b6be249f7a96b06a94d68ed6b",
  "environment": "prod"
}
```

### `service_log_events`
```json
{
  "event_id": "0a71b2f516dbd27eac31c7c0f7bb4e669123f4451118b1a6ec84ee0e9f7d4a3b",
  "ts": "2026-03-13T04:08:57.445102Z",
  "ingested_at": "2026-03-13T04:09:10.002001Z",
  "service": "api",
  "environment": "prod",
  "level": "info",
  "event": "query.api.submit.completed",
  "query_id": "qry-10f4415b6be249f7a96b06a94d68ed6b",
  "workspace_id": "ws-eval-lookup_rn1_001",
  "doc_id": null,
  "run_id": "573ba010b63d4ac5b3d61d0deb1a2921",
  "test_id": "e2e/test_eval_answer_layer_smoke.py::test_authored_answer_layer_smoke_cases_execute_over_real_stack[lookup_rn1_001]",
  "case_id": "lookup_rn1_001",
  "source_kind": "eval",
  "source_path": "data/logs/e2e/runs/session-123/lookup_rn1_001/api.jsonl",
  "line_number": 42,
  "payload": {
    "event": "query.api.submit.completed",
    "service": "api",
    "query_id": "qry-10f4415b6be249f7a96b06a94d68ed6b"
  }
}
```

### `bundle_documents`
```json
{
  "document_id": "bdoc-e80a76de1b6941cf80f7e0f809bd2e0f",
  "query_id": "qry-10f4415b6be249f7a96b06a94d68ed6b",
  "workspace_id": "ws-eval-lookup_rn1_001",
  "run_id": "573ba010b63d4ac5b3d61d0deb1a2921",
  "test_id": "e2e/test_eval_answer_layer_smoke.py::test_authored_answer_layer_smoke_cases_execute_over_real_stack[lookup_rn1_001]",
  "case_id": "lookup_rn1_001",
  "document_kind": "trace",
  "captured_at": "2026-03-13T04:08:57.452898Z",
  "source_path": "data/context/queries/qry-10f4415b6be249f7a96b06a94d68ed6b/trace.json",
  "content_sha256": "6a6f8ee65bf266e6647ebee19ec3bb80b8dd9a9a5e4d325dcf028d0bf94f34a1",
  "payload_bytes": 18342,
  "payload": {
    "query_id": "qry-10f4415b6be249f7a96b06a94d68ed6b",
    "stages": []
  }
}
```

## Retention assumptions
- V1 and early v2 remain local-first.
- Filesystem outputs remain the deepest source of truth for emitted artifacts.
- Postgres is still the primary central persistence layer for metadata,
  relational log correlation, and v2 bundle document retrieval.
- Loki retention can remain operationally shorter than Postgres because durable
  log-event copies also exist in Postgres.
