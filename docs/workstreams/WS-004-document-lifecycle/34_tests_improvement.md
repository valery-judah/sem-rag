# WS-004 Tests Improvement Plan

**Date:** 2026-03-11
**Scope of this note:** detailed plan for strengthening the current WS-004 automated test baseline after the review in `33_test_review.md`, with explicit emphasis on direct coverage and the systemic test set.

## Purpose

The current repo already has broad runnable evidence for the document lifecycle runtime, but the strongest evidence is concentrated in contracts, persistence, artifact storage, and individual stages.

The next improvement pass should not try to make the suite bigger in every direction. It should instead make the suite **more intentionally shaped**:

* add direct tests for coordination seams that currently rely on indirect pipeline coverage
* preserve the fast default suite as the main developer feedback loop
* define a clearer higher-confidence systemic set for runtime wiring and container-backed behavior
* improve depth where behavior is operationally important, not just easy to unit test

## Current baseline

Observed on this branch:

* `make test` passes with `196 passed, 8 deselected`
* the default suite excludes `e2e` tests through pytest configuration
* the repo currently has no numeric coverage gate or `pytest-cov` setup

The current suite shape is roughly:

* strong lower-layer evidence in `tests/contract/`, `tests/persistence/`, `tests/artifacts/`, and `tests/stages/`
* thin direct evidence for runtime coordination in `src/parity/lifecycle/service.py`
* thin direct evidence for orchestration in `src/parity/lifecycle/orchestrator.py`
* thin direct evidence for worker dispatch behavior in `src/parity/lifecycle/worker.py`
* route coverage in `tests/app/` that is useful but still narrow relative to the routes exposed by `src/parity/app/api.py`
* real systemic coverage in `tests/e2e/`, but outside the default run

## Main improvement goals

1. Increase **direct coverage** of runtime coordination logic instead of only proving it through happy-path pipeline tests.
2. Separate the **default developer suite** from the **systemic confidence suite** more explicitly.
3. Add tests where the current code has meaningful branching, cleanup rules, or error mapping.
4. Keep fixture cost controlled so the suite stays fast enough to run routinely.
5. Avoid broadening the suite with low-signal tests for trivial glue.

## Coverage priorities

### 1. Highest priority: lifecycle coordination

The highest-value missing coverage is in the runtime coordination layer:

* `src/parity/lifecycle/service.py`
* `src/parity/lifecycle/orchestrator.py`
* `src/parity/lifecycle/worker.py`

These modules contain behavior that is important, stateful, and only partially exercised directly today:

* job enqueue rules
* active-job detection
* retry eligibility
* retry reset-status mapping
* downstream cleanup on retry
* missing-runner and unexpected-exception handling
* failure event recording and status update semantics

This area should be the first expansion because it closes the largest gap between “the pipeline works” and “the coordination rules are directly defended under tests”.

### 2. Next priority: operator and internal API routes

`src/parity/app/api.py` exposes more than upload:

* `/documents/{doc_id}/status`
* `/documents/{doc_id}/artifacts`
* `/documents/{doc_id}/retry`
* `/retrieval/query`
* `/healthz`
* `/readyz`
* `/internal/run-next-job`

Most of these routes are only covered incidentally today through pipeline tests. They need dedicated route-contract tests for error mapping and operator behavior.

### 3. Next priority: systemic runtime confidence

The repo already has `tests/e2e/`, but it currently sits outside the default feedback loop. That is correct, but the systemic set should be made more intentional:

* clearly identify which tests count as “systemic”
* make sure they cover runtime startup, migrations, API readiness, worker progression, retry, and representative failure behavior
* keep that suite small enough to remain credible and maintainable

### 4. Lower priority: utility and runtime-entrypoint glue

Some modules are light on direct tests:

* `src/parity/runtime.py`
* `src/parity/app/settings.py`
* parts of `src/parity/app/deps.py`

These are worth covering, but after the coordination and route gaps are closed.

## Proposed test-structure changes

The current package split is mostly good and should stay in place.

Recommended additions:

* add `tests/lifecycle/test_service.py`
* add `tests/lifecycle/test_orchestrator.py`
* expand `tests/lifecycle/test_worker.py`
* expand `tests/app/test_documents_api.py` or split it into:
  * `tests/app/test_upload_api.py`
  * `tests/app/test_status_api.py`
  * `tests/app/test_retry_api.py`
  * `tests/app/test_retrieval_api.py`
  * `tests/app/test_runtime_health_api.py`
* add `tests/runtime/test_runtime_entrypoint.py`
* add `tests/app/test_settings.py` only if the settings module becomes meaningfully more complex or if failure modes need to be locked

The structural rule should be:

* `tests/contract/`: semantic invariants and state-machine truth
* `tests/persistence/`: repository and migration truth
* `tests/artifacts/`: durable artifact payload and path truth
* `tests/stages/`: one stage at a time
* `tests/lifecycle/`: coordination rules across repositories, stages, and jobs
* `tests/app/`: HTTP route shape and error mapping
* `tests/pipeline/`: in-process end-to-end document flows
* `tests/e2e/`: container-backed systemic runtime proof
* `tests/runtime/`: command-entrypoint and runtime bootstrapping behavior

## Proposed direct-coverage changes

### A. `tests/lifecycle/test_service.py`

This file should directly exercise `DocumentLifecycleService` without always going through HTTP.

Tests to add:

* `test_upload_document_enqueues_extract_when_orchestrator_is_configured`
* `test_upload_document_accepts_markdown_and_resolves_title_fallback`
* `test_upload_document_rejects_missing_filename`
* `test_upload_document_rejects_non_utf8_markdown`
* `test_get_document_status_reports_first_active_job_stage`
* `test_get_document_status_raises_for_unknown_document`
* `test_query_document_raises_for_unknown_document`
* `test_query_document_requires_vector_store_configuration`
* `test_retry_document_rejects_ready_document`
* `test_retry_document_rejects_non_failed_document`
* `test_retry_document_rejects_when_active_job_exists`
* `test_retry_document_rejects_when_failed_event_has_no_job_stage`
* `test_retry_document_resets_to_registered_for_extract_retry`
* `test_retry_document_resets_to_extracting_for_normalize_retry`
* `test_retry_document_cleans_extracted_normalized_and_derived_state_for_extract_retry`
* `test_retry_document_cleans_normalized_and_derived_state_for_normalize_retry`
* `test_retry_document_cleans_only_derived_state_for_sectionize_retry`
* `test_retry_document_cleans_only_index_state_for_index_retry`
* `test_get_artifact_refs_returns_existing_and_missing_paths_correctly`

Why this matters:

* these are real branch points in the service
* they currently carry meaningful business logic
* the pipeline tests only prove a small subset of them

### B. `tests/lifecycle/test_orchestrator.py`

This file should isolate `DocumentLifecycleOrchestrator`.

Tests to add:

* `test_enqueue_stage_creates_job_when_document_has_no_active_work`
* `test_enqueue_stage_returns_none_when_document_has_active_job`
* `test_next_stage_returns_expected_linear_sequence`
* `test_next_stage_returns_none_after_ready_check`

Why this matters:

* orchestration is currently trusted mostly through indirect behavior
* the mapping is simple but central
* these tests are cheap and lock down job sequencing explicitly

### C. `tests/lifecycle/test_worker.py`

The existing worker test should remain, but the file should become a fuller worker-behavior suite.

Tests to add:

* `test_run_next_returns_none_when_queue_is_empty`
* `test_worker_marks_job_failed_when_stage_runner_is_missing`
* `test_worker_marks_job_failed_on_stage_execution_error`
* `test_worker_wraps_unexpected_exception_as_internal_stage_error`
* `test_worker_marks_job_succeeded_and_enqueues_next_stage`
* `test_worker_does_not_enqueue_when_runner_returns_no_next_stage`
* `test_worker_skips_document_status_update_when_document_row_is_missing`
* `test_worker_does_not_append_duplicate_failure_when_document_already_failed`
* `test_worker_stops_failure_transition_when_invariant_disallows_failed_state`

Why this matters:

* this is the runtime seam that converts stage failures into durable lifecycle truth
* a single existing failure-path test is not enough for the branch count in `worker.py`

## Proposed API-route changes

### `tests/app/`

The app suite should become route-oriented rather than upload-heavy only.

Tests to add or split:

* `test_status_route_returns_404_for_unknown_document`
* `test_artifacts_route_returns_404_for_unknown_document`
* `test_retry_route_returns_404_for_unknown_document`
* `test_retry_route_returns_409_for_ready_document`
* `test_retry_route_returns_409_for_non_failed_document`
* `test_retry_route_returns_202_and_queued_stage_for_failed_document`
* `test_retrieval_query_returns_404_for_unknown_document`
* `test_retrieval_query_validates_positive_k`
* `test_healthz_returns_ok`
* `test_readyz_returns_ok_when_dependencies_load`
* `test_run_next_job_returns_null_payload_when_no_job_exists`
* `test_run_next_job_returns_job_metadata_when_job_runs`
* `test_upload_route_maps_registration_error_to_500`

Why this matters:

* the internal API is part of actual runtime behavior
* route-level error mapping is user-visible to operators even if the API is internal
* several routes currently have no dedicated negative-path tests

## Proposed systemic-set changes

The repo should explicitly treat the test suite as two layers:

### 1. Default suite

Purpose:

* fast, routinely run
* broad enough to catch local regressions
* still excludes container-backed tests

This should continue to include:

* `tests/contract/`
* `tests/persistence/`
* `tests/artifacts/`
* `tests/stages/`
* `tests/lifecycle/`
* `tests/app/`
* `tests/pipeline/`
* current non-lifecycle top-level tests

Expectation:

* this remains the normal `make test` loop
* it should stay comfortably fast

### 2. Systemic confidence suite

Purpose:

* higher-fidelity runtime proof
* exercise the container image, migrations, API process, worker process, and DB wiring together
* confirm that startup and steady-state behavior are not only correct in-process

This should include:

* all current `tests/e2e/`
* runtime-startup and readiness checks
* at least one retry/failure recovery case
* at least one PDF case
* at least one real-markdown-doc case

The systemic set should stay intentionally small. It should not become a second default suite.

## Proposed fixture strategy

The improvement work should keep the current fixture model disciplined.

Use these layers:

* pure in-memory fakes for service/orchestrator/worker branch coverage
* temp filesystem fixtures for artifact-store and route tests
* real SQLite temp DB for in-process runtime tests
* container-backed Postgres plus API/worker processes for systemic tests

Specific guidance:

* prefer synthetic fixtures when the point is branching or cleanup logic
* prefer copied source fixtures or checked-in snapshots when the point is regression pressure
* avoid large fixture corpora unless they are covering a real behavior class that small fixtures miss
* keep PDF fixtures small and behavior-specific

## Proposed coverage-depth improvements

The next pass should emphasize depth in these areas:

### Retry and cleanup semantics

The retry path in `DocumentLifecycleService` has the most important unproven branch set. Direct tests should confirm:

* reset status by target stage
* correct cleanup scope by target stage
* no accidental deletion of upstream evidence
* correct conflict behavior when active jobs exist

### Worker failure normalization

The worker should be tested for:

* missing stage runner
* declared stage execution failure
* unexpected exception safety net
* duplicate-failure suppression
* no-op behavior when queue is empty

### Route-level operator behavior

The app layer should prove:

* 404 mapping
* 409 mapping
* validation failures
* stable shape of route payloads
* operator debug routes behave predictably when nothing is queued

### Systemic runtime startup

The container-backed suite should continue to prove:

* migrations complete
* API reaches `/readyz`
* worker advances jobs without in-process shortcuts
* retrieval works after indexing
* failure and retry behavior still hold in the containerized stack

## Proposed implementation order

### Phase 1: close direct coordination gaps

Add first:

* `tests/lifecycle/test_service.py`
* `tests/lifecycle/test_orchestrator.py`
* expanded `tests/lifecycle/test_worker.py`

Reason:

* highest risk-adjusted value
* cheapest to add
* directly covers the biggest current blind spot

### Phase 2: widen route-level coverage

Add next:

* expanded or split `tests/app/` route tests

Reason:

* locks down runtime-facing behavior
* gives explicit evidence for operator paths already exposed in code

### Phase 3: tighten the systemic set

Then:

* review `tests/e2e/` for overlap and remove only if clearly redundant
* ensure the set includes startup, readiness, Markdown, PDF, retry, and failure coverage
* keep the case count small

Reason:

* this is the highest-fidelity proof, but also the most expensive to maintain

### Phase 4: fill in light glue coverage

Finally:

* `tests/runtime/test_runtime_entrypoint.py`
* any direct settings/deps tests that are still justified after Phases 1-3

Reason:

* lower behavior risk than the coordination and API layers

## Validation plan

For the test additions in this note, the expected validation set is:

* `make test`

If the systemic suite changes:

* `make test`
* `make test-e2e`

If the work changes runtime wiring, pytest config, or test markers:

* `make fmt-check`
* `make lint`
* `make type`
* `make test`
* `make test-e2e`

## Non-goals

This improvement pass should not:

* add a large snapshot corpus without a specific regression problem to solve
* add numeric coverage thresholds before the suite shape is where it needs to be
* move container-backed tests into the default `make test` loop
* replace direct branch tests with only more happy-path pipeline tests
* claim public API guarantees for the internal runtime routes

## Recommended success criteria

This plan should count as successful when:

* lifecycle coordination has direct tests for retry, queueing, cleanup, and failure mapping
* operator routes have explicit negative-path and payload-shape coverage
* the default suite remains fast and green
* the systemic suite remains separate and credible
* the next review can say the remaining risk is mostly scenario breadth, not missing direct coverage of coordination seams
