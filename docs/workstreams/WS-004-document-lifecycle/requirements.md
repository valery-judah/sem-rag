---
artifact_kind: requirements
id: WS-004-R1
title: Document Lifecycle Requirements
status: draft
created: 2026-03-11
updated: 2026-03-11
---

# Document Lifecycle Requirements

## Purpose
Define the requirements for staged delivery of the MVP document lifecycle.

This artifact is a workstream planning document. It must stay aligned with:

- `docs/evergreen/mvp.md` for product scope
- `docs/evergreen/architecture.md` for current implementation truth
- `docs/delivery/workflow.md` for the conceptual lifecycle model

It does not create a public API contract or broaden MVP scope.

## Problem statement
The repo already contains an internal document-processing seam:

`UPLOADED -> REGISTERED -> EXTRACTING -> NORMALIZED -> CHUNKED -> INDEXED -> READY`

That seam is tested, but the runtime behind it does not exist yet. There is no real ingestion pipeline for PDF or Markdown inputs, no parser/normalizer runtime, no chunking pipeline, and no retrieval-ready publication flow over ingested corpora.

The workstream goal is to turn the currently abstract lifecycle into an implemented document pipeline that produces stable, retrievable, inspectable evidence-bearing objects for the later query lifecycle.

## Outcome
WS-004 is complete when the system can accept MVP-supported documents, move them through the document lifecycle, persist the resulting structural and retrieval artifacts, and mark a document `READY` only when it is actually retrievable and traceable back to source.

## Scope
### In scope
- lifecycle delivery for text-based PDF and Markdown inputs only
- document registration and persistent identity
- extraction and normalization into recoverable text structure
- section recovery and chunk production
- provenance-bearing persistence for documents, sections, and chunks
- index publication sufficient to support later retrieval work
- lifecycle state transitions and failure recording
- staged validation that proves each lifecycle step is real

### Out of scope
- answer generation
- user-facing source inspection UI
- stable HTTP, CLI, or package API commitments
- OCR, scanned PDFs, and rich layout understanding
- tables, figures, diagrams, and image-centric extraction
- re-ingestion, supersession, withdrawal, or version-history workflows as MVP requirements
- connector sync, automation, or collaboration features

## Requirements
### R1. Supported inputs
The lifecycle must accept only the MVP-supported source types:

- text-based PDF
- Markdown

Inputs outside those bounds must fail explicitly rather than degrade into undefined processing behavior.

### R2. Stable document identity
Each uploaded source artifact must be registered as a durable document record with:

- stable `doc_id`
- workspace/corpus boundary
- source type
- title and filename
- upload timestamp
- storage reference to the raw artifact
- current ingest status

Identity must survive later processing stages so derived sections and chunks can always resolve back to the owning document.

### R3. Lifecycle state discipline
The implemented pipeline must respect the current locked internal lifecycle seam:

`UPLOADED -> REGISTERED -> EXTRACTING -> NORMALIZED -> CHUNKED -> INDEXED -> READY`

`FAILED` remains the terminal failure state available from each in-flight stage.

The workstream may refine internal execution details, but it must not silently redefine these status semantics without intentional follow-up contract work.

### R4. Recoverable source extraction
The extraction stage must produce text that is recoverable enough for downstream normalization and provenance.

For MVP:

- PDF extraction may be coarse, but it must preserve page-oriented recoverability when available
- Markdown extraction must preserve the source text faithfully enough to retain structural cues
- extraction failures must be explicit and attributable to the document

### R5. Structure-preserving normalization
The normalization stage must transform extracted content into a representation that preserves enough structure for later sectioning and chunking.

At minimum, the normalized representation must preserve or derive:

- document order
- headings and section hierarchy when recoverable
- paragraphs and ordinary text boundaries
- code-block or table-like text as text when present, without claiming rich structure understanding
- offsets or equivalent provenance hooks when available

### R6. Section recovery
The pipeline must produce `Section` records that reflect recoverable document structure.

At minimum:

- every section must belong to exactly one document
- every section must carry a non-empty heading path
- parent-child structure must be reconstructible when present
- page ranges and source offsets should be attached when recoverable

For MVP, section recovery is allowed to be coarse for PDFs as long as it remains useful for later inspection and chunk context.

### R7. Chunk production
The pipeline must produce retrieval-addressable `Chunk` records from normalized content.

Chunks must:

- preserve document ownership
- preserve document order
- carry heading-path context
- remain semantically coherent enough for later retrieval
- carry provenance fields such as page range or source offsets when recoverable

Chunking must favor discourse and section boundaries over naive fixed windows when those boundaries are available.

### R8. Traceability and provenance
Every persisted chunk and section must remain traceable back to its source document.

For MVP, provenance must be recoverable rather than exact-span perfect. Acceptable provenance includes combinations of:

- document identity
- heading path
- section identity
- page range or page label
- source offsets

The system must not mark a document `READY` if it cannot recover enough provenance to support later source inspection at a coarse level.

### R9. Publication and readiness
The indexing/publication step must make produced chunks available for later retrieval work and must only transition a document to `READY` when:

- the document record exists
- normalized structure exists
- chunks exist
- indexed retrieval artifacts exist
- provenance-bearing linkage across document, section, and chunk records is intact

`READY` means retrievable and inspectable enough for the MVP, not merely "processing finished."

### R10. Failure handling
The pipeline must fail honestly and leave enough evidence to diagnose where and why processing stopped.

At minimum, failures must preserve:

- the document identity
- the last reached lifecycle state
- the failure state transition
- an operator-usable failure reason or category

Failure handling must prevent partial artifacts from being mistaken for `READY` content.

### R11. Idempotent stage behavior
The staged pipeline should support safe retries at the document level for non-terminal steps where practical.

For MVP this does not require full re-ingestion/version-history semantics, but it does require enough discipline that repeated processing does not create ambiguous ownership or broken cross-links among document, section, and chunk records.

### R12. Validation surface
Each implemented stage must have validation evidence at the same semantic level as the requirement it satisfies.

Minimum validation expectations:

- contract tests for lifecycle progression and core models
- persistence tests for document, section, and chunk linkage
- pipeline tests that prove PDF and Markdown documents can reach `READY`
- failure-path tests for unsupported or malformed inputs

## Delivery stages
### Stage 1. Registration and lifecycle execution skeleton
Goal:
Make document intake real enough to create durable `Document` records and execute lifecycle transitions through explicit stage runners.

Must deliver:

- document registration from raw input artifacts
- persisted document metadata and ingest status
- lifecycle orchestration with explicit failure transitions
- no-op or placeholder stage boundaries only where needed to keep later stages swappable

Exit signal:
An uploaded PDF or Markdown document can be registered, persisted, and driven through the lifecycle machinery with real status transitions and failure accounting.

### Stage 2. Extraction and normalization
Goal:
Turn raw PDF and Markdown inputs into normalized, provenance-bearing text suitable for structure recovery.

Must deliver:

- Markdown extraction path
- text-based PDF extraction path
- normalized text output with ordering and recoverable structure cues
- explicit extraction/normalization failure reporting

Exit signal:
Representative PDF and Markdown fixtures can reach `NORMALIZED` with inspectable normalized output.

### Stage 3. Structure recovery and chunk production
Goal:
Produce persisted `Section` and `Chunk` artifacts with stable linkage and useful provenance.

Must deliver:

- section derivation from normalized content
- chunking aligned to section/discourse boundaries where possible
- persistence for sections and chunks
- integrity checks across document, section, and chunk records

Exit signal:
Representative documents can reach `CHUNKED`, and the resulting sections/chunks are internally consistent and inspectable.

### Stage 4. Index publication and readiness
Goal:
Publish chunks into the retrieval layer and define the real meaning of document readiness.

Must deliver:

- indexing/publication for produced chunks
- readiness checks tied to persisted artifacts, not only process completion
- retrieval smoke coverage proving indexed content is reachable

Exit signal:
Representative documents can reach `READY`, and later retrieval work can consume the indexed artifacts without bypassing the lifecycle.

## Invariants
- The lifecycle must stay bounded to PDF and Markdown inputs for MVP.
- A `Chunk` or `Section` cannot exist without an owning `Document`.
- `READY` documents must have persisted provenance-bearing artifacts behind them.
- `FAILED` documents must not masquerade as partially ready documents.
- Coarse provenance is acceptable for MVP; missing provenance is not.
- Staged delivery may add implementation seams, but it should minimize churn against the existing internal contract layer unless that contract is intentionally revised.

## Dependencies
- `docs/evergreen/mvp.md`
- `docs/evergreen/architecture.md`
- `docs/delivery/workflow.md`
- `src/parity/_contracts/models.py`
- `src/parity/_contracts/lifecycle.py`
- `src/parity/persistence.py`

## Open questions
- Should normalization produce an explicit intermediate artifact in code, or can section/chunk derivation operate directly from a persisted normalized text representation?
- How much PDF-specific heading inference is necessary to satisfy MVP provenance expectations without overcommitting to layout reconstruction?
- Should indexing be synchronous inside the lifecycle runner for MVP, or modeled as a separate publish step with its own retry boundary?
