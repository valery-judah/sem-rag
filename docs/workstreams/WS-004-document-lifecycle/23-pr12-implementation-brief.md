---
artifact_kind: implementation_brief
id: WS-004-PR12
title: PR 12 Implementation Brief
status: implemented
created: 2026-03-11
updated: 2026-03-11
---

# PR 12 Implementation Brief: End-to-End Validation and Developer Ergonomics

## Summary
- Add end-to-end lifecycle coverage and local runtime commands for the internal app and worker.
- Close the loop from upload to `READY` for both Markdown and PDF fixtures.
- Update evergreen docs so repo truth matches the implemented pipeline.

## Implementation Changes
- Add `tests/pipeline/` end-to-end coverage and `tests/lifecycle/test_worker.py`.
- Add `make run-api` and `make run-worker`.
- Add a `python -m doc_forge.lifecycle.worker` entrypoint and update evergreen docs.

## Invariants
- Developers can start the app and worker locally, upload documents, and observe them reach `READY`.
- Internal health, status, retry, artifact, and retrieval-smoke routes stay testable and operator-focused.
- Evergreen architecture/runbook now describe the implemented lifecycle pipeline rather than the pre-runtime gap.

## Tests
- `tests/lifecycle/test_worker.py`
- `tests/pipeline/test_markdown_to_ready.py`
- `tests/pipeline/test_pdf_to_ready.py`
- `tests/pipeline/test_retry_recovery.py`

## Deferred
- Public API promotion and user-facing inspection UX.
