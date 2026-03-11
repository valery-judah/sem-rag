# WS-004 Test Review

**Date:** 2026-03-11
**Scope of this note:** review of the implemented document-lifecycle pipeline components and the current automated-test baseline relevant to WS-004.

## Executive summary

The current branch contains a substantial implementation of the internal document lifecycle runtime, and the lifecycle-oriented test baseline is now runnable.

Primary finding:

* the missing `parity.artifacts` blocker has been resolved by adding a tracked internal artifact package plus dedicated artifact tests and fixture snapshots
* the default non-e2e repo test target now passes end to end

What is still verifiable today:

* the implemented pipeline shape can be derived from current code
* artifact persistence has a real package and real tests under `src/parity/artifacts/` and `tests/artifacts/`
* the default repo suite passed with `196 passed, 8 deselected in 2.89s`
* the lifecycle-focused suites in `tests/app/`, `tests/lifecycle/`, `tests/stages/`, `tests/pipeline/`, and `tests/contract/test_readiness_contract.py` are now part of earned runnable coverage

This means the repo now has **broad runnable evidence** for WS-004 quality and coverage:

* strong evidence for lifecycle contract rules and persistence integrity
* earned evidence for artifact-backed stage/runtime behavior
* runnable proof for the lifecycle path from registration through readiness

## Implemented base components of the pipeline

The base document-lifecycle pipeline already implemented in code is:

1. **Internal transport and intake**
   * `src/parity/app/api.py`
   * upload, status, artifact inspection, retry, retrieval-smoke, health, and worker-debug routes

2. **Lifecycle coordination**
   * `src/parity/lifecycle/service.py`
   * validates uploads, resolves source type, registers documents, exposes status/query/retry operations

3. **Document-scoped job orchestration**
   * `src/parity/lifecycle/orchestrator.py`
   * queues the next lifecycle job when no active work exists

4. **Worker execution**
   * `src/parity/lifecycle/worker.py`
   * claims queued jobs, dispatches stage runners, records failure events, and queues downstream stages

5. **Stage runner seam**
   * `src/parity/stages/base.py`
   * common `StageRunner` protocol plus `StageExecutionError` failure mapping

6. **Stage pipeline**
   * `src/parity/stages/register.py`
   * `src/parity/stages/extract.py`
   * `src/parity/stages/normalize.py`
   * `src/parity/stages/sectionize.py`
   * `src/parity/stages/chunk.py`
   * `src/parity/stages/index.py`
   * `src/parity/stages/ready.py`

7. **Format-specific processing services**
   * extractors for Markdown and PDF
   * normalizers for Markdown and PDF

8. **Structure and retrieval-preparation services**
   * `src/parity/structure/sections.py`
   * `src/parity/chunking/service.py`
   * `src/parity/indexing/vector_store.py`
   * `src/parity/lifecycle/readiness.py`

9. **Persistence and durable lifecycle truth**
   * document, lifecycle-event, job, section, chunk, index-entry, and chunk-embedding repositories under `src/parity/persistence/`

The intended stage flow is:

`REGISTERED -> EXTRACTING -> NORMALIZED -> CHUNKED -> INDEXED -> READY`

with retry and failure handling layered on top of document-scoped jobs.

## Artifact layer now present

The earlier mismatch between imports and tracked files has been resolved:

* `src/parity/artifacts/` now exists and is the internal package for:
  * `RawArtifactRef`
  * `ExtractedArtifact`
  * `ExtractedArtifactPage`
  * `ExtractedArtifactBlock`
  * `NormalizedArtifact`
  * `NormalizedArtifactBlock`
  * `FilesystemArtifactStore`
* `tests/artifacts/` now exists and covers:
  * raw artifact store behavior
  * extracted artifact store behavior
  * normalized artifact store behavior
  * normalized payload regressions using copied Markdown fixtures

The fixture bundle now includes:

* a small synthetic smoke Markdown source
* a copied `design-exploration.md` source fixture
* a copied `mvp.md` source fixture
* checked-in extracted and normalized golden snapshots for those sources

## Test baseline observed in this clone

### Default repo validation

User-provided validation result on this branch:

* `make test`
* result: `196 passed, 8 deselected in 2.89s`

Observed result:

* the default non-e2e suite is green

What this proves:

* lifecycle state-machine semantics exist and are enforced
* `_contracts` seam compatibility is covered
* lifecycle runtime models are covered
* artifact persistence is covered
* persistence linkage, ordering, replacement semantics, and integrity constraints are covered
* vector publication persistence and smoke-query behavior are covered at the repository/vector-store layer
* stage, worker, API, readiness, and pipeline tests are runnable

### Artifact-specific coverage now present

Artifact-store and snapshot coverage now exists in tracked repo tests:

* `tests/artifacts/test_raw_artifact_store.py`
* `tests/artifacts/test_extracted_artifact_store.py`
* `tests/artifacts/test_normalized_artifact_store.py`
* `tests/artifacts/test_normalized_payload_regressions.py`

What those tests prove:

* raw bytes round-trip for Markdown and PDF
* deterministic managed-root path generation
* delete and overwrite semantics
* extracted and normalized JSON round-trips
* schema validation on load
* golden regression pressure over copied Markdown fixtures

### Lifecycle-focused coverage now runnable

The previously blocked WS-004-relevant suites are now part of earned coverage:

* `tests/app/test_documents_api.py`
* `tests/lifecycle/test_worker.py`
* `tests/contract/test_readiness_contract.py`
* `tests/stages/`
* `tests/pipeline/`

These suites now provide runnable coverage for:

* upload acceptance and rejection behavior
* worker-side failure recording
* register, extract, normalize, sectionize, chunk, index, and ready stages
* Markdown and PDF pipeline happy paths
* retry recovery
* multi-document retrieval scoping
* readiness invariants
* coarse provenance / source navigation guarantees

## Coverage assessment by subsystem

### 1. Lifecycle contract and status semantics

Current quality:

* strong

Evidence:

* explicit tests exist for status sets, legal transitions, illegal transitions, lifecycle models, and `_contracts` seam compatibility

Residual risk:

* low at the pure contract layer

### 2. Persistence integrity and retry replacement

Current quality:

* strong

Evidence:

* document, section, chunk, index-entry, chunk-embedding, lifecycle-event, job, migration, integrity-constraint, and replace-on-retry tests all run

Residual risk:

* low to moderate, mostly in environment-specific runtime behavior rather than basic persistence semantics

### 3. Artifact persistence layer

Current quality:

* strong

Evidence:

* tracked artifact package exists
* dedicated artifact-store and golden regression tests exist
* artifact-backed lifecycle suites are now runnable

Residual risk:

* moderate, because snapshot coverage is intentionally small and Markdown-only in this slice

### 4. Stage runners

Current quality:

* strong

Evidence:

* register stage: identity, raw linkage, checksum, idempotency, rollback, cleanup
* extract stage: Markdown ordering and offsets, PDF page handling, malformed/sparse PDF failures
* normalize stage: Markdown and PDF structural normalization behavior
* section stage: Markdown hierarchy and PDF synthetic fallback
* chunk stage: chunk persistence and chunked status transition
* index stage: full publication and partial-publication cleanup
* ready stage: provenance and retrieval-smoke requirements

Residual risk:

* moderate, mostly around breadth of adversarial fixtures rather than absence of execution proof

### 5. End-to-end lifecycle pipeline

Current quality:

* good

Evidence:

* Markdown reaches `READY`
* PDF reaches `READY`
* retry recovers failed extraction
* retrieval remains document-scoped
* ready chunks retain coarse traceability

Residual risk:

* moderate, because the default suite still covers a compact scenario set and the docker-backed e2e suite is outside the default run

### 6. Worker and operator routes

Current quality:

* good

Evidence:

* worker failure-path coverage exists and runs
* API upload/rejection/status coverage exists and runs

Residual risk:

* moderate, mainly around deeper retry/operator scenarios rather than missing basic coverage

## Test quality observations

Positive signals:

* the lifecycle suite is organized around invariants and durable evidence rather than implementation trivia
* contract, artifact, persistence, stage, and pipeline coverage are meaningfully separated
* artifact snapshots are now based on copied fixtures rather than live docs, which reduces drift
* the default repo validation is green

Negative signals:

* `docs/workstreams/WS-004-document-lifecycle/workstream.md` and `32_status.md` are materially behind current code truth in opposite directions:
  * `workstream.md` still says the runtime pipeline does not exist
  * `32_status.md` still says stage/runtime/artifact work was not implemented
* the artifact snapshot corpus is intentionally small, so coverage breadth is still limited

## Main findings for external expert review

1. **The artifact blocker is gone.**
   The lifecycle runtime now has a tracked artifact subsystem and dedicated artifact tests, and the lifecycle-oriented suites are runnable.

2. **WS-004 now has earned end-to-end non-e2e test evidence.**
   The default repo suite passed with `196 passed, 8 deselected`, which means lifecycle, stage, readiness, and pipeline behavior now count as runnable proof rather than authored intent.

3. **The strongest remaining test-quality questions are about breadth, not existence.**
   The main expert review question is now whether the current scenario set is sufficiently deep across malformed inputs, retries, and real-document variation, not whether the artifact-backed lifecycle exists.

4. **Documentation currently mixes implemented truth, stale workstream framing, and missing proof points.**
   An expert assessing test adequacy should treat current code and actual runnable tests as authoritative over older workstream notes that still describe the runtime as missing.

## Commands and observations used for this review

Commands run:

* `make test`
* prior targeted repo inspection and suite-collection commands used during the earlier review pass

Observed outcomes:

* `make test` passed with `196 passed, 8 deselected in 2.89s`
* artifact package and artifact tests are present in the repo
* lifecycle-focused suites are now runnable instead of blocked at collection

## Recommendation

If this review is handed to an external expert, frame the repo state like this:

* implemented lifecycle architecture exists in code
* artifact-backed runtime proof exists and is exercised under the default non-e2e suite
* lower-layer lifecycle evidence and higher-layer stage/pipeline evidence are both present
* the next quality question is coverage depth and scenario adequacy, especially around failure breadth, retries, and larger real-document fixture diversity
