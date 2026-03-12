# WS-004 Status

**Date:** 2026-03-11
**Scope of this note:** handoff status after implementing the test refactor that was requested from `30_tests_refactor.md` and `31_pytest_plan.md`.

## What was completed

The repo now has the **PR1-aligned contract and persistence test layout** that matches the parts of the plan the codebase can actually support today.

Completed changes:

* flat test files were replaced with package-based test layout:
  * `tests/contract/`
  * `tests/persistence/`
* lifecycle contract coverage was split into focused files:
  * status-set tests
  * state-machine tests
  * lifecycle runtime model tests
  * `_contracts` seam compatibility tests
  * contract model validation tests
* persistence coverage was split into focused files:
  * document repository tests
  * section repository tests
  * chunk repository tests
  * integrity constraint tests
  * replace-on-retry tests
* `src/doc_forge/persistence.py` was extended with:
  * `replace_sections_for_document(...)`
  * `replace_chunks_for_document(...)`
  * stronger document-scoped relational integrity via composite foreign keys for section parent links and chunk-to-section links
* `pyproject.toml` now defines pytest markers for:
  * `contract`
  * `persistence`
* `docs/evergreen/architecture.md` was updated so the repo map points to the new test locations instead of the deleted flat files.

## Validation completed

These commands were run successfully on 2026-03-11:

* `make test`
* `make lint`
* `make type`

At the end of the change set, the suite reported `107 passed`.

## What was intentionally not implemented

The broader `31_pytest_plan.md` includes many stage, artifact, readiness, and pipeline tests. Those were **not** added yet.

Still not implemented in code:

* PR 2 persistence package conversion
* Postgres-backed repositories
* Alembic migrations
* `lifecycle_events` durable storage
* `document_jobs` durable storage
* artifact store for raw/extracted/normalized files
* registration, extraction, normalization, sectioning, chunking, indexing, readiness stage runners
* end-to-end document lifecycle pipeline
* readiness predicate service and retrieval smoke path

## Why those items were deferred

The current repo does not implement the runtime seams those tests would exercise.

Important constraint:

* `docs/evergreen/architecture.md` still says ingestion, parsing, normalization, chunk retrieval over ingested corpora, answer generation, and inspection APIs are **not implemented**.

Because of that, the work in this turn stayed inside the boundary of implemented repo truth:

* strengthen the lifecycle contract tests
* strengthen persistence integrity and retry semantics in the current SQLite seam
* do not add stage or pipeline tests that would only be placeholders
* do not describe PR2+ behavior as already implemented

## Current repo state relevant to the next agent

Files deleted as part of the test refactor:

* `tests/test_contracts.py`
* `tests/test_contract_seam.py`
* `tests/test_lifecycle.py`
* `tests/test_persistence_contracts.py`

Replacement locations:

* `tests/contract/test_contract_models.py`
* `tests/contract/test_processing_status_sets.py`
* `tests/contract/test_lifecycle_state_machine.py`
* `tests/contract/test_lifecycle_models.py`
* `tests/contract/test_contract_seam_compat.py`
* `tests/persistence/test_document_repository.py`
* `tests/persistence/test_section_repository.py`
* `tests/persistence/test_chunk_repository.py`
* `tests/persistence/test_integrity_constraints.py`
* `tests/persistence/test_replace_on_retry.py`

If an IDE tab still points at `tests/test_contracts.py`, it is stale. The replacement is `tests/contract/test_contract_models.py`.

## Workstream docs present now

Relevant docs in this folder as of 2026-03-11:

* `22-staged.md`
* `23-pr1-implementation-brief.md`
* `23-pr2-implementation-brief.md`
* `30_tests_refactor.md`
* `31_pytest_plan.md`

`23-pr2-implementation-brief.md` exists and is the most concrete starting point for the next implementation step.

## Recommended next step

The next agent should start **PR 2: Persistence foundation and artifact store**, using:

* `docs/workstreams/WS-004-document-lifecycle/22-staged.md`
* `docs/workstreams/WS-004-document-lifecycle/23-pr2-implementation-brief.md`

Recommended implementation order:

1. convert `src/doc_forge/persistence.py` into a `src/doc_forge/persistence/` package while preserving current import compatibility from `doc_forge.persistence`
2. move the current SQLite helpers into a compatibility module
3. add the new Postgres schema/repository seams for documents, lifecycle events, and document jobs
4. add filesystem-backed artifact store seams for raw, extracted, and normalized artifacts
5. add PR2 tests without deleting the SQLite compatibility coverage

## Practical caution for the next agent

Do not remove the current SQLite-backed seam yet. It is still the only implemented persistence path exercised by the repo, and the new test layout now depends on it.

Do not add stage or pipeline tests until the corresponding runtime seams exist in `src/doc_forge/`.
