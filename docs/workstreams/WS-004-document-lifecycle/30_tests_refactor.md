I would build this around **lifecycle invariants**, not around endpoints.

For this MVP, the trust contract is: stable document identity, explicit stage semantics, provenance-bearing artifacts, honest failure behavior, and `READY` only when the document is actually retrievable and inspectable. The lifecycle design also makes status authoritative and requires stage completion to correspond to durable evidence. That means the test suite should primarily prove **state correctness + persisted artifact correctness + retry correctness**, with HTTP tests kept thin.  

## 1. Start with a hard state-machine contract

This is the cheapest place to catch bad behavior, and PR1 already narrows the contract: `FAILED` should only be reachable from in-flight statuses, and `UPLOADED -> FAILED` should be rejected. I would make this the first test module and treat it as the canonical guardrail for the whole subsystem. 

What I would test here:

* legal forward transitions only:

  * `UPLOADED -> REGISTERED`
  * `REGISTERED -> EXTRACTING`
  * `EXTRACTING -> NORMALIZED`
  * `NORMALIZED -> CHUNKED`
  * `CHUNKED -> INDEXED`
  * `INDEXED -> READY`
* legal failure transitions only from in-flight states:

  * `REGISTERED|EXTRACTING|NORMALIZED|CHUNKED|INDEXED -> FAILED`
* illegal transitions rejected:

  * skips like `REGISTERED -> CHUNKED`
  * regressions like `READY -> CHUNKED`
  * duplicate terminal churn like `FAILED -> READY`
  * explicitly `UPLOADED -> FAILED` per PR1
* terminal-state behavior:

  * once `READY`, only explicit future reingestion flow should move it
  * once `FAILED`, retry must go through the defined retry entrypoint, not arbitrary mutation

I would make these mostly **pure tests** against `state_machine.py`, with a small parameterized matrix. This should run in milliseconds.

## 2. Test each stage runner against its exit invariant

The design doc is clear that each stage only counts as complete if its required artifact or invariant exists durably. So every stage runner needs tests that prove both:

1. it does the work, and
2. it does **not** advance state unless persistence succeeded. 

I would write stage-runner tests like this:

### Registration

Assert that success creates:

* stable `Document`
* raw artifact linkage
* lifecycle event
* next job enqueue

And that failure does **not** leave a half-registered document marked `REGISTERED`. 

### Extraction

Assert that success creates a persisted extracted artifact and moves to `EXTRACTING`/next-stage progression correctly. Failure cases should include malformed PDF, no usable text layer, decode failure, extractor exception. 

### Normalization

Assert that a normalized artifact is persisted, order is preserved, and source-specific structure is handled conservatively. Also assert that the stage does not mark `NORMALIZED` if artifact write fails. 

### Chunking / section recovery

Assert that persisted `Section` and `Chunk` records exist, are linked correctly, and satisfy the integrity checks before status becomes `CHUNKED`. 

### Indexing

Assert that every active chunk gets a publication record and that `INDEXED` is not set unless publication completeness holds. 

### Readiness

Assert that `READY` is impossible unless all required artifacts exist, linkage is intact, provenance minimums are met, and retrieval smoke passes. This is one of the most important tests in the suite because it prevents “looks done” from drifting away from “is usable.”

## 3. Make persistence/integrity tests first-class

For this system, storage bugs are lifecycle bugs. I would not treat repository tests as incidental.

The design explicitly requires:

* no orphan chunks
* every chunk belongs to one section and one document
* replace-on-retry semantics
* index entries matching the active chunk set
* stable ordering and linkage. 

So I would create a dedicated persistence test module that uses a real test database and verifies:

* FK and uniqueness constraints
* `replace_for_document` semantics actually replace instead of append
* retry after partial failure does not duplicate sections/chunks/index entries
* document-scoped delete-and-republish for indexing works
* lifecycle events are append-only and ordered enough for operator inspection

This is where many MVP systems fail: retries “work” functionally but silently accumulate duplicated children.

## 4. Add a small number of end-to-end pipeline tests with real fixtures

The architecture doc already calls out the required pipeline cases. I would keep this set small, stable, and close to product reality. 

Minimum E2E fixtures:

* one well-structured Markdown file that should reach `READY`
* one text-based PDF with recoverable pages/headings that should reach `READY`
* one malformed or text-layer-broken PDF that should reach `FAILED`
* one unsupported input type rejected before lifecycle progression

Each E2E test should assert more than the final status. It should also verify:

* artifacts exist where expected
* section/chunk counts are non-zero where appropriate
* provenance fields exist
* retrieval smoke returns at least one hit from the document before `READY` is granted.

## 5. Put a lot of effort into retry and partial-failure tests

This subsystem is stage-oriented, so the dangerous bugs are almost always around **partial writes** and **resume behavior**, not the happy path.

I would explicitly simulate failures at these boundaries:

* after raw artifact write but before document registration
* after document creation but before lifecycle event append
* after extracted artifact write but before status update
* after sections persist but before chunks persist
* after chunks persist but before index publication completes
* after index entries persist but before readiness evaluation

For each case, test:

* resulting status
* preserved failure detail
* whether partial artifacts remain inspectable
* whether retry replaces downstream artifacts cleanly
* whether a second retry is idempotent. 

If this area is weak, the system will produce the worst kind of bug: documents that are neither clearly failed nor actually usable.

## 6. Keep seam-compatibility tests for PR1

PR1 explicitly says `_contracts` remains the compatibility seam and asks for seam tests to prove import-site stability while lifecycle internals move into `parity.lifecycle`. I would keep a focused test module that imports through both old and new locations and verifies identity/behavior parity for the moved types and helpers. 

That module should cover:

* `ProcessingStatus`
* in-flight / terminal status sets
* transition validation helpers
* lifecycle errors
* any runtime lifecycle models exposed internally in PR1

This is not glamorous, but it prevents churn across the codebase while refactoring.

## 7. Use fixture strategy deliberately

I would use three categories of fixtures:

### Golden document fixtures

Stable input documents with expected normalized structure, section tree, and chunk set. These are for regression detection.

### Corrupt / adversarial fixtures

Malformed PDFs, sparse-text PDFs, Markdown with broken heading levels, giant code blocks, repeated headers/footers.

### Synthetic persistence fixtures

Factory-generated `Document`, `Section`, `Chunk`, `LifecycleEvent`, `IndexEntry` rows for repository and readiness tests.

For golden fixtures, I would snapshot **normalized artifacts and section/chunk metadata**, not full embeddings or volatile timestamps.

## 8. Separate fake-backed tests from real-backed smoke tests

I would use fakes for most unit/stage tests:

* fake artifact store
* fake extractor/normalizer
* fake vector index
* deterministic token counter

But I would still keep a narrow band of real-backed smoke tests:

* real filesystem writes
* real test Postgres
* real vector publication adapter or a near-real test double at the repository boundary
* real retrieval smoke call for the readiness path. 

That gives you speed for most of the suite and realism where the trust contract depends on actual integration.

## 9. Bias the suite toward invariant assertions, not implementation trivia

I would avoid tests like “method X called method Y once.” For this domain, the important assertions are:

* which status did we end in?
* which artifacts exist?
* what linkage exists?
* can this be retried safely?
* does `READY` actually mean retrievable?

That keeps the tests robust through refactors.

## 10. Concrete suite layout

I would organize it roughly like this:

* `tests/contract/test_lifecycle_state_machine.py`
* `tests/contract/test_lifecycle_models.py`
* `tests/contract/test_contract_seam_compat.py`
* `tests/stages/test_register_stage.py`
* `tests/stages/test_extract_stage.py`
* `tests/stages/test_normalize_stage.py`
* `tests/stages/test_chunk_stage.py`
* `tests/stages/test_index_stage.py`
* `tests/stages/test_ready_stage.py`
* `tests/persistence/test_document_repos.py`
* `tests/persistence/test_replace_on_retry.py`
* `tests/persistence/test_integrity_constraints.py`
* `tests/pipeline/test_markdown_to_ready.py`
* `tests/pipeline/test_pdf_to_ready.py`
* `tests/pipeline/test_pdf_failure_paths.py`
* `tests/pipeline/test_retry_recovery.py`

## 11. What I would implement first

In order:

1. state-machine contract tests
2. readiness predicate tests
3. replace-on-retry persistence tests
4. one Markdown happy-path pipeline
5. one malformed-PDF failure path
6. seam-compatibility tests from PR1
7. PDF happy-path pipeline last

That ordering gives fast signal on the most structurally important behavior before spending time on PDF-specific complexity.

The sharp version is: **prove the lifecycle contract, then prove durable evidence, then prove retries, then prove the pipeline.** That matches the architecture docs and keeps the MVP honest.
