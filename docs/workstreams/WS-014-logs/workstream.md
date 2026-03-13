---
artifact_kind: workstream
id: WS-014
title: Logs
work_type: feature
status: active
owner:
created: 2026-03-13
updated: 2026-03-13
---

# Summary
Add eval-ready structured logging across the API, lifecycle service, worker, and
ingestion stages without changing the stable HTTP contract or adding a new persisted
log store.

## Objective
Make runtime logs machine-parseable enough for evals and operator debugging, with
stable event names, correlation IDs, compact counters, and redaction-safe payloads.

## Non-goals
- No new HTTP request or response fields.
- No new database-backed log persistence layer.
- No duplication of full query trace payloads into logs.
- No attempt to resolve unrelated pre-existing lint issues outside the logging change set.

## Current status
- Implemented route-boundary logs in the FastAPI layer for:
  `readyz`, document upload, document delete, document retry, retrieval smoke,
  query submission, query review routes, and `run-next-job`.
- Extended lifecycle logging in the document service for upload validation,
  retrieval smoke summaries, delete summaries, and retry eligibility / queueing.
- Added worker and orchestrator logs so document ingestion can be reconstructed via
  `worker.run_next.*`, `worker.job.*`, and enqueue events.
- Added stage-level ingestion logs for `extract`, `normalize`, `sectionize`,
  `chunk`, `index`, and `ready_check`.
- Preserved the existing query runtime logs as the canonical query-path backbone and
  filled the missing API-boundary events around them with `query.api.*`.
- Added targeted tests covering the new log surface for API, worker, and selected
  stage behavior.
- The repo-wide `make test` and `make type` pass with the refactor.
- The repo-wide `make lint` target still reports unrelated pre-existing `E501`
  findings in files outside the main logging implementation path.

## Next step
- Decide whether the next iteration should standardize log schema helpers to reduce
  repeated event-shaping code across API and lifecycle modules.

## Relevant context
- paths:
  - `src/doc_forge/app/api.py`
  - `src/doc_forge/lifecycle/service.py`
  - `src/doc_forge/lifecycle/orchestrator.py`
  - `src/doc_forge/lifecycle/worker.py`
  - `src/doc_forge/stages/`
  - `tests/app/test_runtime_api.py`
  - `tests/lifecycle/test_worker.py`
- components:
  - FastAPI request middleware and route handlers
  - document lifecycle service
  - lifecycle worker and orchestrator
  - ingestion stage runners
  - existing query runtime / trace review flow
- constraints:
  - keep logs redaction-safe
  - keep event names stable enough for eval parsing
  - avoid contract changes on stable public routes
  - complement durable query traces instead of replacing them
- read first:
  - `docs/evergreen/api-contracts.md`
  - `docs/evergreen/architecture.md`

## Workflow steps
1. Frame the feature scope and relevant constraints.
2. Shape the implementation and validation approach.
3. Execute and validate the workstream.

## Validation
- `make fmt-check`
- `make type`
- `make test`
- `uv run ruff check` over the modified logging files and targeted tests
- known repo-level limitation:
  `make lint` still fails on unrelated long-line findings already present in
  `src/doc_forge/evaluation/answer_layer.py`,
  `e2e/test_query_runtime_smoke.py`, and
  `tests/evaluation/test_e2e_eval_support.py`

## Linked artifacts
- `docs/workstreams/WS-014-logs/notes.md`
- `docs/evergreen/api-contracts.md`
- `docs/evergreen/architecture.md`
