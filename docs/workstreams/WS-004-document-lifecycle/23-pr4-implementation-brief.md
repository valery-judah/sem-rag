---
artifact_kind: implementation_brief
id: WS-004-PR4
title: PR 4 Implementation Brief
status: implemented
created: 2026-03-11
updated: 2026-03-11
---

# PR 4 Implementation Brief: Job Orchestration and Worker Skeleton

## Summary
- Add document-scoped job orchestration, queue claiming, stage dispatch, and worker failure handling.
- Extend upload so successful registration also enqueues the first `EXTRACT` job.
- Keep the runtime internal-only and preserve the locked lifecycle status seam.

## Implementation Changes
- Add `src/parity/lifecycle/orchestrator.py` and `src/parity/lifecycle/worker.py`.
- Add `src/parity/stages/base.py` for shared stage runner and failure types.
- Extend `DocumentJobRepository` with queue claim, active-job, succeed, and fail helpers.
- Wire orchestration into `DocumentLifecycleService.upload_document(...)`.

## Invariants
- Worker dispatch is stage-name based.
- Failures update the document to `FAILED` and append a failed lifecycle event.
- Successful registration leaves one queued `EXTRACT` job and no duplicate active jobs.

## Tests
- Queue/job repository behavior under claim, succeed, and fail flows.
- Worker failure handling via `tests/lifecycle/test_worker.py`.
- Upload path still passes route and registration tests.

## Deferred
- Real stage implementations beyond registration.
- Retry route and readiness semantics.
