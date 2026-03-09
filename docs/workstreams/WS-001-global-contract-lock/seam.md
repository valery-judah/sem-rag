# WS-001 Contract Seam

## Purpose

This note defines the Phase 1 contract seam for `WS-001`. It is an implementation note for the seam tests, not a replacement for the canonical contract spec in `contract-lock.md`.

The seam exists to prove that the locked Phase 1 shared objects compose cleanly across domains without pulling real upload, parsing, retrieval, or answer-generation runtime work into WS-001.

The executable seam starts from an already-uploaded, already-processed corpus. It models the final path where a user asks a question over several documents and the contract layer returns either a source-backed answer or an honest insufficient-evidence result.

## Phase Boundary

- Phase 1 seam: prove the contracts fit together over fixtures and in-memory objects
- Phase 3 walking skeleton: prove the real integrated path from upload to source-backed answer

This seam must stay thinner than the walking skeleton.

## Scope

The seam must exercise the locked internal models:

1. `Document`
2. `Section`
3. `Chunk`
4. `SourceReference`
5. `RetrievalHit`
6. `Answer`
7. document lifecycle semantics

The seam must be implemented in `tests/test_contract_seam.py`.

## Reusable Mock Seam Helper

The executable mock seam helper for WS-001 lives in `tests/support/contract_seam.py`.

It is test-only and exists to prove that the locked shared objects compose cleanly over deterministic fixtures. It is not a runtime abstraction, and later phases must not promote it into production ingestion, retrieval, or answer-generation code.

## Locked Scenarios

### 1. Supported-answer seam

Build a valid cross-document answer path over fixtures:

1. create a small ready corpus of uploaded `Document` objects
2. create `Section` and `Chunk` objects across that corpus
3. simulate a user question as a plain string
4. create two `SourceReference` objects from two different documents
5. create two `RetrievalHit` objects
6. create one `Answer(status="supported")` citing both documents

Pass criteria:

- all objects validate with the locked required fields
- the `SourceReference` resolves to at least `doc_id`, `document_title`, and `snippet`
- the `supported` answer contains citations from two different documents
- missing heading and page precision remain allowed
- the seam does not imply unsupported precision beyond the supplied fields

### 2. Insufficient-evidence seam

Build the smallest valid negative path over the same corpus:

1. reuse the same base corpus
2. simulate a user question with no usable retrieval support
3. create one `Answer(status="insufficient_evidence")`

Pass criteria:

- the outcome validates as a first-class answer, not as an exception path
- `answer_text` is present
- `insufficiency_note` is present
- `source_references` is explicitly `[]`

### 3. Lifecycle seam

Validate the locked lifecycle path:

`uploaded -> registered -> extracting -> normalized -> chunked -> indexed -> ready`

Also validate:

- failure from an in-progress state to `failed`
- no transitions out of `ready`
- no transitions out of `failed`

## Non-goals

The seam must not depend on:

- real upload endpoints
- real PDF heading inference
- real chunking heuristics
- embeddings or vector search
- prompt tuning
- evaluation harness design
- production observability

## Related Artifacts

- `contract-lock.md`: semantic source of truth for the Phase 1 contract
- `tests/test_contracts.py`: field, enum, and transition validation
- `tests/support/contract_seam.py`: reusable test-only corpus-question seam helper
- `tests/test_contract_seam.py`: supported-answer, insufficient-evidence, retrieval-trace, and lifecycle seam tests
