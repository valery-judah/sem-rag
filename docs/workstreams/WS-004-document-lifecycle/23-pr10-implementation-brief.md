---
artifact_kind: implementation_brief
id: WS-004-PR10
title: PR 10 Implementation Brief
status: implemented
created: 2026-03-11
updated: 2026-03-11
---

# PR 10 Implementation Brief: Readiness Predicate and Retrieval Smoke Coverage

## Summary
- Define `READY` as a persisted artifact plus retrieval smoke predicate, not a process-complete flag.
- Add an internal readiness service and readiness stage runner.
- Expose internal status, artifact, and retrieval-smoke routes for operator/debug use.

## Implementation Changes
- Add `src/doc_forge/lifecycle/readiness.py` and `src/doc_forge/stages/ready.py`.
- Extend `src/doc_forge/app/api.py` with status, artifact, retrieval-smoke, health, and ready routes.
- Extend `DocumentLifecycleService` with document status and internal query helpers.

## Invariants
- `READY` requires normalized artifacts, sections, chunks, index entries, intact chunk-to-section linkage, and a successful smoke query.
- Documents lacking provenance-bearing linkage cannot become ready.
- The new routes remain internal-only and do not alter `docs/evergreen/api-contracts.md`.

## Tests
- `tests/stages/test_ready_stage.py`
- `tests/pipeline/test_markdown_to_ready.py`
- `tests/pipeline/test_pdf_to_ready.py`

## Deferred
- Stable public query interfaces and answer generation.
