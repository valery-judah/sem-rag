# Schema Sketch: Central Eval Observability

## Summary
This document sketches the v1 relational metadata schema and Loki label model
for central query/eval observability.

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
  - `(case_id)`
  - `(run_id)`
  - `(test_id)`
  - `(workspace_id)`
  - `(source_kind, collected_at desc)`

### `query_context_assets`
- one row per indexed bundle asset path
- columns:
  - `query_id text not null`
  - `asset_kind text not null`
  - `relative_path text null`
  - `present boolean not null`
  - `missing_reason text null`
- keys:
  - foreign key to `query_context_runs(query_id)`
  - unique `(query_id, asset_kind)`

### `eval_case_results`
- one row per eval-scored case/run
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
- keys:
  - foreign key to `query_context_runs(query_id)`
  - unique `(query_id, case_id)`
- indexes:
  - `(case_id, trust_outcome)`
  - `(trust_outcome)`

### `log_sources`
- one row per raw attached log file referenced by a query bundle
- columns:
  - `query_id text not null`
  - `service text not null`
  - `source_path text not null`
  - `matched_line_count integer not null`
- keys:
  - foreign key to `query_context_runs(query_id)`
  - unique `(query_id, service, source_path)`
- indexes:
  - `(service)`
  - `(query_id, service)`

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

## Loki labels
### Required labels
- `service`
- `environment`

### Recommended labels when present in the parsed JSON
- `query_id`
- `workspace_id`
- `doc_id`
- `run_id`
- `test_id`
- `case_id`
- `source_kind`

## Example Postgres row
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

## Example Loki event labels
```json
{
  "service": "api",
  "environment": "prod",
  "query_id": "qry-10f4415b6be249f7a96b06a94d68ed6b",
  "workspace_id": "ws-eval-lookup_rn1_001",
  "run_id": "573ba010b63d4ac5b3d61d0deb1a2921",
  "test_id": "e2e/test_eval_answer_layer_smoke.py::test_authored_answer_layer_smoke_cases_execute_over_real_stack[lookup_rn1_001]",
  "case_id": "lookup_rn1_001",
  "source_kind": "eval"
}
```

## Retention assumptions
- V1 is local-first.
- Raw logs and raw bundles remain on disk and are the deepest source of truth.
- Postgres stores searchable indexes and summary fields only.
- Loki retention can stay short-to-medium in v1 because raw JSONL logs remain on
  disk outside Loki.
