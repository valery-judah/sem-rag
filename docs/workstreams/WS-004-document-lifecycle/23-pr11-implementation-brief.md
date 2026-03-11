---
artifact_kind: implementation_brief
id: WS-004-PR11
title: PR 11 Implementation Brief
status: implemented
created: 2026-03-11
updated: 2026-03-11
---

# PR 11 Implementation Brief: Retry Semantics, Replacement Behavior, and Failure Hardening

## Summary
- Add document-level retry over failed lifecycle stages.
- Reset documents to the correct pre-stage status and clear only downstream derived artifacts.
- Reject retries when a document is ready or already has active queued/running work.

## Implementation Changes
- Extend `DocumentLifecycleService` with `retry_document(...)`.
- Add internal `POST /documents/{doc_id}/retry`.
- Reuse artifact-store deletes plus section/chunk/index/embedding replacement for cleanup.

## Invariants
- Retries preserve stable document identity.
- Retries derive the target stage from the latest failed lifecycle event detail.
- Partial downstream artifacts are removed before requeueing the failed stage.

## Tests
- `tests/pipeline/test_retry_recovery.py`
- Existing replace-on-retry persistence coverage continues to validate ownership rules.

## Deferred
- Re-ingestion/version history, cancellation, and distributed worker coordination.
