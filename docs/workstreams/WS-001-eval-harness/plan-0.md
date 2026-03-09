# MVP Evaluation Harness v1

## Summary
Build a deterministic, pytest-first evaluation harness that protects the MVP trust invariants already described in [`mvp.md`](/home/val/projects/sem-rag/docs/evergreen/mvp.md): supported cross-document answers, inspectable provenance, and honest insufficient-evidence behavior. The first slice will not target a future ingest pipeline or expose a user-facing eval CLI; it will run against committed synthetic fixtures and today’s contract seam plus retrieval demo.

## Implementation Changes
- Add an internal evaluation package under `src/parity/evaluation/` and keep it out of `parity.__all__` so the public stable API remains unchanged.
- Define internal harness types:
  - `EvaluationCase`: case id, scenario name, question, expected outcome (`supported` or `insufficient_evidence`), expected supporting doc/chunk ids, and provenance expectations.
  - `CaseResult`: pass/fail, failed assertions, and the actual retrieved/supporting ids observed.
  - `SystemUnderTest` protocol: deterministic callable that executes one case and returns retrieval hits plus answer payloads in the existing contract shapes.
- Implement a baseline deterministic adapter over the existing corpus-question seam fixtures so the harness can evaluate answer/evidence behavior without pretending the full MVP runtime already exists.
- Seed the harness with a small committed synthetic dataset derived from current seam fixtures:
  - supported cross-document answer
  - insufficient-evidence / abstention case
  - provenance completeness case that verifies minimum inspectable reference fields and PDF-vs-Markdown differences
- Keep `SemanticIndex` retrieval tests as a separate low-level guard, but add one harness-level retrieval expectation that asserts stable supporting chunk/doc ordering for the supported scenario.
- Reuse or refactor the current seam fixture builders in `tests/support/` only as needed so there is one canonical synthetic corpus/question source, not parallel fixture systems.
- Keep invocation pytest-only in the first pass: no CLI command, no aggregate score report, no benchmark thresholds beyond case pass/fail.

## Tests
- Add harness unit tests that verify:
  - cases validate required expectations
  - the runner records assertion failures clearly
  - deterministic ordering and provenance mismatches are reported against the correct case id
- Add baseline evaluation tests that execute all committed cases through the deterministic adapter and fail on any invariant regression.
- Retain and, where needed, extend direct unit tests for `SemanticIndex` so ranking behavior is still covered independently of the higher-level harness.
- Run `make test` as the mandatory validation for this slice.

## Public Interfaces / Contracts
- No changes to the stable public API documented in [`api-contracts.md`](/home/val/projects/sem-rag/docs/evergreen/api-contracts.md).
- New evaluation modules are internal-only and should not be exported from `parity` top-level imports.
- Existing internal contract models (`Answer`, `RetrievalHit`, `SourceReference`, etc.) remain the payload format used by the harness; no new evergreen runtime contract should be documented yet.

## Assumptions And Defaults
- The first harness is a regression gate, not a model-comparison framework.
- Synthetic in-repo fixtures are the source of truth for baseline eval cases; real PDF/Markdown sample files are deferred.
- The harness should cover MVP trust semantics before broadening into ingestion/parsing metrics.
- Because the repo does not yet implement real answer generation or ingestion, the deterministic seam is the correct initial system-under-test.
