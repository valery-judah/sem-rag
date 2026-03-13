---
artifact_kind: workstream
id: WS-015
title: Context Collecting
work_type: feature
status: active
owner:
created: 2026-03-13
updated: 2026-03-13
---

# Summary
Add a query-centric context collection layer that ties together archived
container logs, persisted query review payloads, replay bundles, and optional
eval metadata so operators and eval workflows can reopen one query and inspect
the full story quickly.

## Objective
Make one `query_id` enough to reopen the useful debug and eval context for a
run without scanning raw Docker logs, querying the database manually, or
reconstructing the run from separate temp artifacts.

## Non-goals
- No public HTTP API changes.
- No new database-backed log store.
- No distributed tracing or OpenTelemetry backend.
- No attempt to solve retrieval correctness or answer quality in this workstream.

## Current status
- Query context bundles exist under `data/context/queries/<query_id>/`.
- The collector writes:
  `manifest.json`, `summary.json`, `trace.json`, `citations.json`,
  `replay.json`, `query-response.json`, filtered `logs/query-events.jsonl`,
  and symlinked raw `logs/api.jsonl` / `logs/worker.jsonl` when available.
- Eval-driven e2e runs additionally write:
  `eval-result.json` and `execution-metadata.json`.
- Repo-local JSONL container log archives already exist under `data/logs/` for:
  compose runs and docker-backed e2e runs.
- Internal operator surfaces already exist:
  `make collect-query-context QUERY_ID=<query_id>` and
  `make show-query-context QUERY_ID=<query_id>`.
- The collector is useful enough to diagnose query behavior and eval outcomes.
- The fresh compose experiment also surfaced a meaningful runtime issue:
  one supported query produced a semantically wrong direct answer while the
  collected bundle still showed a clean, internally consistent run.
- Non-eval collection now reconstructs `query-response.json` from persisted
  final artifacts, so compose and plain `e2e` bundles expose the final public
  answer payload directly.
- Compose defaults are now aligned with the app defaults:
  `DOC_FORGE_ANSWER_GENERATOR_BACKEND=deterministic` unless explicitly
  overridden for Ollama-backed experiments.

## Next step
- Use the collected compose bundle for
  `qry-f5fac35f6862463986d8ea7dc74bd3a3` to debug the retrieval / selection /
  support mismatch that produced a semantically wrong direct answer.

## Relevant context
- paths:
  - `src/doc_forge/query/context_archive.py`
  - `src/doc_forge/devtools/query_context.py`
  - `e2e/eval_support.py`
  - `data/context/queries/`
  - `data/logs/`
- components:
  - query review service
  - query replay service
  - repo-local JSONL container log archive
  - query-context collector and CLI
  - e2e eval artifact writer
- constraints:
  - stay filesystem-first
  - keep `query_id` as the primary lookup key
  - preserve current JSON log and review payload shapes
  - represent missing assets explicitly in `manifest.json`
- read first:
  - `docs/evergreen/runbook.md`
  - `docs/evergreen/architecture.md`
  - `docs/workstreams/WS-006-query-lifecycle/18_stage-8-trace-review-replay-logging-design.md`
  - `docs/workstreams/WS-014-logs/workstream.md`

## Workflow steps
1. Keep the collector usable for both operator debugging and eval analysis.
2. Use real collected bundles to validate that the indexed context is sufficient.
3. Fix the highest-value gaps revealed by collected-bundle experiments.

## Validation
- `uv run pytest tests/query/test_query_context_archive.py tests/test_query_context_cli.py -q`
- `uv run ruff check src/doc_forge/query/context_archive.py tests/query/test_query_context_archive.py tests/test_query_context_cli.py`
- experiment evidence:
  existing bundles plus one fresh compose query bundle were inspected directly
  through `data/context/queries/`.

## Linked artifacts
- `docs/workstreams/WS-015-context-collecting/current-plan.md`
- `docs/workstreams/WS-014-logs/workstream.md`
- `docs/evergreen/runbook.md`
- `src/doc_forge/query/context_archive.py`
- `src/doc_forge/devtools/query_context.py`
