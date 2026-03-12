# Workstream 012: E2E Test Refactor and Invariant Tightening

## Motivation
The original `tests/e2e/test_real_markdown_docs.py` covered the markdown ingestion happy path, but it mixed low-level HTTP details into scenario tests and blurred the line between what the suite actually proved and what it merely intended to prove.

This workstream refactors the markdown E2E suite so that:

- scenario tests read as product behaviors rather than transport scripts;
- invariants are explicit and named;
- helper logic lives in a single test-side DSL module; and
- the documented invariants match the assertions that really run today.

The goal is not a wholesale E2E harness redesign. The goal is to make the current suite more trustworthy by removing false confidence and tightening the contract it documents.

## Reasoning and Principles

### 1. Scenario-first test language
The suite now prefers behavior-oriented tests such as `test_given_single_markdown_when_uploaded_then_ready_and_queryable` over imperative scripts with embedded transport detail.

- Principle: E2E tests should read as runtime contracts.
- Result: the markdown test module focuses on scenario intent, while the support module owns upload, wait, query, and delete mechanics.

### 2. Single test-side DSL
The support layer in `tests/e2e/support.py` is the canonical helper surface for this markdown E2E suite.

- Principle: scenario tests should not duplicate `httpx` calls, raw response parsing, or artifact/status shaping.
- Result: the DSL now exposes typed `UploadReceipt`, `DocumentStatus`, `ArtifactRefs`, `QueryResult`, and `E2EReadyDocument` models, plus separate submit-vs-ingest flows.

### 3. Explicit invariants over implied intent
The workstream now documents only the invariants the suite currently enforces.

- Principle: an invariant is only valid documentation if a failing system would actually break the test.
- Result: the invariant list below intentionally avoids claiming rollback, timeout, or full database-cascade coverage that the suite does not yet assert.

### 4. Parameterization and isolation
Real markdown document cases remain parameterized so failures stay local to each asset.

- Principle: one bad document should not hide the status of the others.
- Result: the single-document readiness and provenance checks each execute independently per real markdown case.

---

## Core Properties and Invariants Tested

1. **Pipeline lifecycle property**
   Markdown documents progress from upload to terminal `ready` within a bounded polling window and become queryable through the retrieval smoke endpoint.

2. **Artifact integrity invariant**
   A ready markdown document publishes all three expected artifact layers on disk:
   `raw`, `extracted`, and `normalized`.

3. **Strict vector mapping invariant**
   Ready documents have non-zero retrieval material and preserve a strict 1:1:1 mapping:
   `chunk_count == embedding_count == index_entry_count`.

4. **Retrieval isolation invariant**
   Doc-scoped retrieval remains isolated to the requested `doc_id`.
   The suite verifies this both for sequential multi-document uploads and for concurrent uploads with unique marker text.

5. **Chunk provenance invariant**
   Every chunk retains at least one recoverable source pointer:
   `section_id`, `page_start`, or `source_start_offset`.

6. **Deletion cleanup invariant**
   Deleting a ready document removes its filesystem artifacts and clears its retrieval material from the vector snapshot for that `doc_id`.

   Note: the current markdown E2E suite does not additionally assert `404` on subsequent document fetches or inspect lifecycle/job table cleanup directly.

7. **Duplicate upload safety invariant**
   Re-uploading identical markdown content must not corrupt the original document state.
   The suite accepts either of the currently valid contract shapes:
   a clean duplicate rejection (`409`) or a second successful ingestion with a distinct `doc_id`.
   In both cases, the original document remains queryable and internally consistent.

8. **Early markdown rejection invariant**
   Invalid UTF-8 markdown is rejected synchronously with `415 Unsupported Media Type`, preventing it from entering async ingestion.

   Note: this is early input validation coverage, not rollback coverage for a partially processed document.

9. **Concurrent upload isolation invariant**
   Concurrent markdown uploads with unique marker text remain isolated at both storage and retrieval boundaries.
   Each uploaded document preserves its own chunk text, its own 1:1:1 vector mapping, and its own doc-scoped query behavior without marker leakage from sibling uploads.

10. **Semantic ordering invariant**
    For a deterministic three-chunk markdown fixture, retrieval with `k=3` returns three hits sorted by descending score, and the semantically relevant chunk ranks ahead of the distractor chunks.

    Note: this is a smoke-level ordering check over the current internal vector store, not a general ranking-quality benchmark.

---

## Implementation Summary

1. **Support-layer consolidation**
   - Added `tests/e2e/support.py` as the shared markdown E2E DSL.
   - Moved upload, wait, artifact lookup, query, and delete operations behind `SystemDriver`.
   - Added typed test models for upload receipts, document status, artifact refs, and retrieval hits.

2. **Scenario cleanup in `test_real_markdown_docs.py`**
   - Kept the parameterized ready-and-queryable coverage for real markdown assets.
   - Kept provenance coverage for real markdown assets.
   - Routed deletion coverage through the DSL instead of raw `client` plumbing.
   - Removed special-case synthetic artifact assertions and now require the full artifact set for ready markdown uploads.

3. **Invariant tightening**
   - Reworked duplicate-upload coverage so it tolerates both a valid `409` duplicate rejection and a valid second successful ingestion.
   - Reworked concurrency coverage to assert marker isolation in chunk text and doc-scoped queries, not just successful completion.
   - Reworked semantic ordering coverage to use a deterministic three-chunk fixture that the current markdown pipeline actually emits.
   - Renamed the invalid-markdown case around early rejection instead of describing it as partial-failure rollback.

## Validation

The following targeted E2E validation was run after the refactor:

- `uv run pytest tests/e2e/test_real_markdown_docs.py -m e2e -q`
- `uv run pytest tests/e2e/test_stack_failures.py -m e2e -q`
- `uv run pytest tests/e2e/test_pdf_stack.py -m e2e -q`

These checks confirm that the refactored markdown E2E suite stays aligned with adjacent failure-path and PDF-path coverage.

## Known Gaps

The current workstream intentionally does not add coverage for:

- ingestion timeout or stalled-pipeline behavior;
- rollback after asynchronous mid-pipeline failure for markdown documents;
- post-delete `404` document fetch assertions;
- direct inspection of lifecycle/job row cleanup after deletion; or
- broad ranking evaluation beyond the deterministic smoke fixture.

Those remain follow-up candidates if the team wants to extend this suite from contract validation into deeper resilience coverage.
