# Notes

## 2026-03-13: eval-ready logging refactor

Implemented the first pass of `WS-014` with the goal of making runtime logs useful
for eval pipelines and operator debugging without changing the stable API surface.

### What changed

- Added route-boundary events in `src/doc_forge/app/api.py` for:
  - `system.readyz.*`
  - `document.upload.*`
  - `document.delete.*`
  - `document.retry.*`
  - `retrieval.smoke.*`
  - `query.api.*`
  - `review.summary.loaded`
  - `review.trace.loaded`
  - `review.citations.loaded`
  - `review.lookup_failed`
  - `worker.run_next.*`
- Added lifecycle service logs in `src/doc_forge/lifecycle/service.py` for:
  - upload validation / registration
  - retrieval smoke execution summary
  - delete execution summary
  - retry eligibility rejection and queueing
- Added worker / orchestrator logs in:
  - `src/doc_forge/lifecycle/orchestrator.py`
  - `src/doc_forge/lifecycle/worker.py`
- Added stage-level start / completion / failure logs in:
  - `src/doc_forge/stages/extract.py`
  - `src/doc_forge/stages/normalize.py`
  - `src/doc_forge/stages/sectionize.py`
  - `src/doc_forge/stages/chunk.py`
  - `src/doc_forge/stages/index.py`
  - `src/doc_forge/stages/ready.py`

### Logging shape

- Reused the existing JSON `structlog` pipeline.
- Standardized around low-cardinality fields where available:
  `event`, `request_id`, `workspace_id`, `doc_id`, `query_id`, `job_id`,
  `stage_name`, `http_status`, `status`, `duration_ms`, `error_code`, and
  compact counters.
- Avoided raw question text, answer text, chunk text, or artifact contents in logs.
- Used hashes and lengths for free-text request inputs where needed.

### Validation and coverage

- Added / updated targeted tests in:
  - `tests/app/test_runtime_api.py`
  - `tests/lifecycle/test_worker.py`
- Verified:
  - `make fmt-check`
  - `make type`
  - `make test`
  - `uv run ruff check` on the modified logging files and tests

### Remaining follow-up

- `make lint` still reports unrelated long-line findings outside the main logging
  implementation path.
- If log schema repetition starts growing, extract helper utilities for shared
  event construction rather than continuing to hand-shape payloads inline.
