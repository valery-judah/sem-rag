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
- Consolidate lifecycle semantics into a dedicated internal `doc_forge.lifecycle` package.
- Keep `src/doc_forge/_contracts/` as the current internal seam for shared models and existing repo consumers.
- Tighten lifecycle failure semantics so `FAILED` is reachable only from in-flight statuses.

## Implementation Changes
- Keep `Document`, `Section`, `Chunk`, and `SourceType` in `src/doc_forge/_contracts/models.py`.
- Add `src/doc_forge/lifecycle/status.py` as the canonical home for `ProcessingStatus`, `IN_FLIGHT_PROCESSING_STATUSES`, and `TERMINAL_PROCESSING_STATUSES`.
- Add `src/doc_forge/lifecycle/state_machine.py` as the single source of truth for legal status transitions and lifecycle validation helpers.
- Add `src/doc_forge/lifecycle/models.py` for storage-independent runtime lifecycle types: `LifecycleEvent`, `LifecycleStage`, and `FailureCategory`.
- Add `src/doc_forge/lifecycle/errors.py` for `InvalidLifecycleTransitionError` and `LifecycleInvariantError`.
- Keep shared corpus and answer models importable from `src/doc_forge/_contracts/` in PR 1 because persistence, evaluation, and tests already depend on that namespace.
- Keep `src/doc_forge/_contracts/lifecycle.py` as the internal compatibility re-export over `doc_forge.lifecycle`.
- Remove `UPLOADED -> FAILED` from the legal transition graph.

## Public And Internal Boundaries
- Do not rename `ProcessingStatus` to `DocumentStatus`.
- Do not create a parallel `src/doc_forge/domain/document.py` layer in PR 1.
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
- Migrate all internal imports in `src/doc_forge/persistence.py`, `src/doc_forge/evaluation/`, and tests to that final namespace in one coordinated pass.
- Update evergreen architecture and workstream docs that currently name `_contracts`.
- Delete `src/doc_forge/_contracts/` only after code imports and docs have both been switched.
- Avoid partial namespace splits unless the repo intentionally decides to keep `doc_forge.lifecycle` separate while shared models remain under `_contracts`.
