# Document Lifecycle Staged Delivery Plan

## Purpose

Turn the document lifecycle design into a bounded execution plan for stacked PRs.

This document is guidance for implementation sequencing and review. It is not the design authority and it does not create a public API contract.

Primary references:

* `docs/workstreams/WS-004-document-lifecycle/requirements.md`
* `docs/workstreams/WS-004-document-lifecycle/21-design-exploration.md`

## Recommended execution unit

Use **stacked PRs** as the primary implementation unit.

Why this fits this workstream:

* the lifecycle requirements are staged already
* each stage has a clear semantic exit signal
* the coding agent will perform better with bounded, reviewable deltas
* failures are easier to localize when each PR introduces one new invariant layer
* the team can stop after any completed slice and still retain a coherent partial system

Avoid one large pipeline PR. It will be harder to review, harder to debug, and more likely to blur lifecycle semantics.

Also avoid ultra-small mechanical PRs that do not produce a meaningful seam.

## PR sizing rule

Each PR should satisfy all of the following:

* introduces one primary architectural seam or one lifecycle milestone
* leaves the repo in a runnable, testable state
* includes tests at the same semantic level as the added capability
* avoids introducing placeholder abstractions that are not exercised immediately
* stays narrow enough that a reviewer can understand the change in one sitting

A good target is **7 to 12 PRs** total for this workstream.

## Review policy for the coding agent

For each PR, require the agent to include:

* purpose
* exact files expected to change
* invariants added or enforced
* tests added
* what is intentionally deferred to the next PR

This helps prevent accidental scope bleed into retrieval, answer generation, or public API design.

## PR plan

### PR 1. Core domain and lifecycle contract enforcement

Implementation brief:
* `docs/workstreams/WS-004-document-lifecycle/23-pr1-implementation-brief.md`

Purpose:
Make the lifecycle and core entity boundaries explicit in code before any real pipeline logic lands.

Deliverables:

* define or refine core models for:
  * `Document`
  * `DocumentStatus`
  * `LifecycleEvent`
  * stage and failure categories
* define legal lifecycle transitions
* implement lifecycle validation utilities
* add a single source of truth for status progression
* consolidate lifecycle logic while keeping `_contracts` as the current internal seam for shared models

Likely files:

* `src/parity/lifecycle/state_machine.py`
* `src/parity/lifecycle/errors.py`
* `src/parity/lifecycle/models.py`
* alignment points with `src/parity/_contracts/...`

Tests:

* allowed transitions pass
* illegal transitions fail
* `FAILED` is reachable only from in-flight states as intended
* status semantics remain aligned with the existing seam

Exit condition:
The repo has an executable lifecycle contract independent of storage or pipeline execution.

Deferred follow-up:
* namespace cleanup that removes `_contracts` only after a coordinated import and docs migration in a later PR

### PR 2. Persistence foundation and artifact store

Purpose:
Introduce the persistence primitives needed for all later stages without yet implementing extraction or chunking.

Deliverables:

* Postgres models and migrations for:
  * `documents`
  * `lifecycle_events`
  * `document_jobs`
* artifact store abstraction for:
  * raw artifacts
  * extracted artifacts
  * normalized artifacts
* repository interfaces and initial implementations
* filesystem layout for artifact storage

Likely files:

* `src/parity/persistence/models.py`
* `src/parity/persistence/repositories.py`
* `src/parity/persistence/migrations/...`
* `src/parity/artifacts/store.py`
* `src/parity/artifacts/schemas.py`

Tests:

* migration smoke test
* document repository round-trip tests
* artifact store write/read tests
* lifecycle event persistence tests

Exit condition:
The repo can persist documents, jobs, lifecycle events, and raw/intermediate artifacts.

### PR 3. Intake path and registration stage

Purpose:
Make upload and registration real enough to create durable document records and raw artifact references.

Deliverables:

* internal HTTP intake path
* supported type validation for PDF and Markdown only
* checksum generation
* raw artifact persistence
* document registration into `REGISTERED`
* lifecycle event creation
* explicit rejection of unsupported inputs

Likely files:

* `src/parity/lifecycle/service.py`
* `src/parity/stages/register.py`
* `src/parity/app/api.py`

Tests:

* PDF upload registers successfully
* Markdown upload registers successfully
* unsupported type fails explicitly
* raw storage path is persisted
* lifecycle event trail is recorded

Exit condition:
An uploaded source becomes a durable `Document` with stable identity and persisted raw artifact linkage.

### PR 4. Job orchestration and worker skeleton

Purpose:
Make stage execution explicit and retryable before the real transformation stages arrive.

Deliverables:

* Postgres-backed job queue logic
* worker loop
* job claiming and status updates
* dispatch by stage name
* explicit failure capture and transition to `FAILED`
* placeholder stage runners only where necessary

Likely files:

* `src/parity/lifecycle/orchestrator.py`
* `src/parity/persistence/jobs.py`
* `src/parity/stages/base.py`
* `src/parity/lifecycle/worker.py`

Tests:

* queued job can be claimed and run
* stage failure records `FAILED`
* retryable vs terminal error handling behaves as expected
* worker does not skip lifecycle validation

Exit condition:
A registered document can move through explicit stage machinery with real failure accounting.

### PR 5. Extraction paths for Markdown and PDF

Purpose:
Implement recoverable extraction for the two supported input types.

Deliverables:

* Markdown extractor
* text-PDF extractor
* extracted artifact schema and persistence
* extraction warnings and explicit failure reporting
* page-aware extraction metadata for PDFs when available

Likely files:

* `src/parity/extractors/base.py`
* `src/parity/extractors/markdown.py`
* `src/parity/extractors/pdf.py`
* `src/parity/stages/extract.py`

Tests:

* Markdown fixture extracts with preserved text cues
* text-PDF fixture extracts with page-aware structure
* malformed PDF fails explicitly
* extracted artifacts are inspectable and attributable to the document

Exit condition:
Representative PDF and Markdown inputs can produce durable extracted artifacts.

### PR 6. Normalization and normalized artifact persistence

Purpose:
Convert extracted content into the canonical intermediate representation that later stages consume.

Deliverables:

* normalized payload schema
* Markdown normalizer
* PDF normalizer
* conservative PDF heading inference policy
* preservation of order, paragraphs, code blocks, and provenance hooks where available
* persisted normalized artifact
* transition to `NORMALIZED`

Likely files:

* `src/parity/normalizers/base.py`
* `src/parity/normalizers/markdown.py`
* `src/parity/normalizers/pdf.py`
* `src/parity/stages/normalize.py`
* `src/parity/artifacts/schemas.py`

Tests:

* Markdown normalization produces expected heading and block structure
* PDF normalization preserves page and order information
* normalized artifacts are persisted and inspectable
* failure reporting is explicit when normalization cannot proceed

Exit condition:
Representative fixtures can reach `NORMALIZED` with real normalized output.

### PR 7. Section recovery and section persistence

Purpose:
Turn normalized structure into stable `Section` records before chunking enters the picture.

Deliverables:

* section derivation service
* heading-path generation
* parent-child relationship reconstruction where supported
* coarse synthetic sections for weakly structured PDFs
* section persistence and replacement-on-retry semantics

Likely files:

* `src/parity/structure/sections.py`
* `src/parity/stages/sectionize.py`
* repository additions in the persistence layer

Tests:

* every section belongs to one document
* heading paths are non-empty
* Markdown hierarchy reconstructs correctly for representative fixtures
* coarse PDF sections are still useful and attributable

Exit condition:
A normalized document can produce persisted, inspectable `Section` records with stable ownership.

### PR 8. Chunk production and integrity checks

Purpose:
Produce retrieval-addressable `Chunk` records with stable provenance and ordering.

Deliverables:

* chunking policy implementation
* section-first chunk derivation
* code-block preservation when practical
* token counting utility
* chunk persistence
* integrity checks across document, section, and chunk ownership
* transition to `CHUNKED`

Likely files:

* `src/parity/chunking/policy.py`
* `src/parity/chunking/service.py`
* `src/parity/stages/chunk.py`
* chunk repository additions

Tests:

* chunks preserve ownership and order
* heading-path context is attached
* chunking favors section and discourse boundaries over naive splits where available
* no orphan chunks exist
* representative fixtures reach `CHUNKED`

Exit condition:
Representative documents can reach `CHUNKED`, and sections and chunks are internally consistent and inspectable.

### PR 9. Embeddings, vector persistence, and `INDEXED` semantics

Purpose:
Publish chunks into a real retrieval backend without expanding into broader query architecture.

Deliverables:

* embedding adapter interface
* Postgres-backed vector persistence and retrieval adapter
* index publication service
* `IndexEntry` persistence
* replace-or-delete publication semantics for retries
* transition to `INDEXED`

Likely files:

* `src/parity/indexing/base.py`
* `src/parity/indexing/embeddings.py`
* `src/parity/indexing/vector_store.py`
* `src/parity/stages/index.py`

Tests:

* all chunks for a document can be published
* index entries are persisted and match the active chunk set
* re-publication does not create ambiguous ownership
* indexing failures transition cleanly to `FAILED`

Exit condition:
A `CHUNKED` document can be published into the retrieval layer and prove index presence through persisted entries.

### PR 10. Readiness predicate and retrieval smoke coverage

Purpose:
Define the real meaning of `READY` and enforce it as code.

Deliverables:

* readiness evaluation service
* invariant checks over normalized artifact, sections, chunks, and index entries
* minimum provenance checks
* a real retrieval smoke path via queryable internal retrieval
* transition to `READY`

Likely files:

* `src/parity/lifecycle/readiness.py`
* `src/parity/stages/ready.py`
* internal inspection or retrieval endpoint support in `src/parity/app/api.py`

Tests:

* document cannot become `READY` without indexed chunks
* document cannot become `READY` without provenance-bearing linkage
* retrieval smoke path returns at least one chunk for the document
* `FAILED` documents cannot masquerade as ready

Exit condition:
Representative PDF and Markdown fixtures can reach `READY` with real retrievability and inspectability guarantees.

### PR 11. Retry semantics, replacement behavior, and failure hardening

Purpose:
Make the pipeline operationally safe for repeated execution on the same document without introducing full version-history semantics.

Deliverables:

* document-level retry entry point
* retry rules per stage
* replace-on-retry behavior for sections, chunks, and index entries
* clearer failure categories and operator-visible diagnostics
* explicit handling of partial artifact preservation

Likely files:

* `src/parity/lifecycle/service.py`
* `src/parity/lifecycle/errors.py`
* persistence repository methods for replacement behavior

Tests:

* retry after extraction failure works correctly
* retry after chunk or index failure does not duplicate ownership
* partial artifacts do not satisfy readiness
* failure details remain inspectable

Exit condition:
The staged pipeline supports safe retries at document scope for non-terminal failures.

### PR 12. End-to-end validation and developer ergonomics

Purpose:
Close the loop with fixtures, commands, and minimal inspection surfaces that make the pipeline usable by engineers.

Deliverables:

* end-to-end pipeline tests from upload to `READY`
* representative PDF and Markdown fixtures committed or referenced in test data
* local dev commands for worker and service start
* basic health and readiness endpoints
* optional artifact inspection endpoint for debugging

Likely files:

* `tests/pipeline/...`
* `tests/fixtures/...`
* `src/parity/app/api.py`
* `Makefile`
* `docker-compose.yml` if used

Tests:

* full happy path for Markdown
* full happy path for text-PDF
* malformed or unsupported input failure paths
* persistence integrity checks at end-to-end level

Exit condition:
A developer can run the service locally, ingest representative fixtures, and observe documents reach `READY` through the full staged lifecycle.

## Alternative grouping when the team wants fewer PRs

If 12 PRs feels too fine-grained for the repo cadence, compress into **8 PRs** by merging these pairs:

* merge PR 1 and PR 2 if the domain and persistence boundary stays reviewable
* merge PR 3 and PR 4 if intake and orchestration are implemented together
* merge PR 5 and PR 6
* merge PR 7 and PR 8
* merge PR 9 and PR 10 only if the readiness predicate is still reviewed explicitly

Do not merge chunking and indexing into a single unreviewed blob. That tends to obscure the difference between `structured` and `retrievable`.

## Recommended order for the coding agent

1. PR 1: lifecycle contract
2. PR 2: persistence foundation
3. PR 3: intake and registration
4. PR 4: worker and orchestration
5. PR 5: extraction
6. PR 6: normalization
7. PR 7: sections
8. PR 8: chunks
9. PR 9: indexing
10. PR 10: readiness
11. PR 11: retry and hardening
12. PR 12: end-to-end ergonomics

## Instructions for the coding agent per PR

For each PR, ask the agent to do all of the following in one pass:

* restate the invariant the PR is meant to establish
* list the exact modules it intends to touch
* implement only the minimum needed to satisfy the PR exit condition
* add tests that prove the new invariant
* leave TODOs only when the next PR has already been named as the owner of that work

Useful prompt pattern:

```text
Implement PR N from the document lifecycle plan.
Focus only on the stated purpose, deliverables, and exit condition.
Do not broaden MVP scope.
Do not add public API commitments unless the PR explicitly requires an internal endpoint.
Add tests at the same semantic level as the PR's invariant.
At the end, summarize:
1. files changed,
2. invariants enforced,
3. tests added,
4. what remains for PR N+1.
```

## Final recommendation

Use **stacked PRs** as the working unit.

For this repo, the most effective granularity is:

* small enough that each PR establishes one new invariant layer
* large enough that each PR leaves behind a runnable, reviewable vertical slice

If you want the highest-signal path with the coding agent, start with PR 1 through PR 4 before touching extraction. That forces the runtime seams, persistence, and failure model to stabilize first, which reduces rework in the content-processing stages.
