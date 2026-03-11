---
artifact_kind: implementation_brief
id: WS-004-PR1
title: PR 1 Implementation Brief
status: draft
created: 2026-03-11
updated: 2026-03-11
---

# PR 1 Implementation Brief: Lifecycle Contract Consolidation

## Summary
- Consolidate lifecycle semantics into a dedicated internal `parity.lifecycle` package.
- Keep `src/parity/_contracts/` as the current internal seam for shared models and existing repo consumers.
- Tighten lifecycle failure semantics so `FAILED` is reachable only from in-flight statuses.

## Implementation Changes
- Keep `Document`, `Section`, `Chunk`, and `SourceType` in `src/parity/_contracts/models.py`.
- Add `src/parity/lifecycle/status.py` as the canonical home for `ProcessingStatus`, `IN_FLIGHT_PROCESSING_STATUSES`, and `TERMINAL_PROCESSING_STATUSES`.
- Add `src/parity/lifecycle/state_machine.py` as the single source of truth for legal status transitions and lifecycle validation helpers.
- Add `src/parity/lifecycle/models.py` for storage-independent runtime lifecycle types: `LifecycleEvent`, `LifecycleStage`, and `FailureCategory`.
- Add `src/parity/lifecycle/errors.py` for `InvalidLifecycleTransitionError` and `LifecycleInvariantError`.
- Keep shared corpus and answer models importable from `src/parity/_contracts/` in PR 1 because persistence, evaluation, and tests already depend on that namespace.
- Keep `src/parity/_contracts/lifecycle.py` as the internal compatibility re-export over `parity.lifecycle`.
- Remove `UPLOADED -> FAILED` from the legal transition graph.

## Public And Internal Boundaries
- Do not rename `ProcessingStatus` to `DocumentStatus`.
- Do not create a parallel `src/parity/domain/document.py` layer in PR 1.
- Do not change the `Document` field set in PR 1; `storage_ref` and `ingest_status` remain unchanged.
- `LifecycleEvent`, `LifecycleStage`, and `FailureCategory` are internal runtime types only and do not become stable public API.
- Do not describe `_contracts` as a temporary shim to be deleted in this PR; it remains the current internal import boundary.

## Tests
- Update contract tests to keep the linear lifecycle path and reject `UPLOADED -> FAILED`.
- Add focused lifecycle model tests for `LifecycleEvent`, `LifecycleStage`, and `FailureCategory`.
- Keep persistence and contract seam tests passing without import-site churn as evidence that `_contracts` remains a working compatibility boundary.

## Deferred
- Persistence tables or migrations for lifecycle events.
- Job orchestration, retries, or worker runtime.
- Intake-path fields such as checksum or raw storage path renames.

## Follow-up Refactor PR
- Choose a final home for shared models outside `_contracts` before any namespace migration begins.
- Migrate all internal imports in `src/parity/persistence.py`, `src/parity/evaluation/`, and tests to that final namespace in one coordinated pass.
- Update evergreen architecture and workstream docs that currently name `_contracts`.
- Delete `src/parity/_contracts/` only after code imports and docs have both been switched.
- Avoid partial namespace splits unless the repo intentionally decides to keep `parity.lifecycle` separate while shared models remain under `_contracts`.
