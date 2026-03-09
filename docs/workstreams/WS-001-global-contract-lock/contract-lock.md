# Contract Lock RFC: WS-001 Global Contract Lock

**Status:** Draft
**Scope:** MVP / Phase 1 Global Contract Lock
**Last updated:** 2026-03-09

## 1. Context And Purpose

This RFC is the canonical Phase 1 artifact for `WS-001`. Its purpose is to lock the minimum shared internal contracts required for parallel MVP implementation.

This RFC is derived from **Phase 1 — Global Contract Lock** in [post-mvp-framing-workflow-v2.md](../../../../../docs/delivery/post-mvp-framing-workflow-v2.md). It should be read as the concrete local execution of that phase inside this repository.

This phase is intentionally narrow. It does not freeze the full service architecture, public API endpoints, parsing heuristics, retrieval tuning, prompt wording, or evaluation design. It only locks the cross-domain contracts whose ambiguity would block Data Platform & Ingestion, Parsing & Structural Normalization, Search & Grounded Generation, and Product Surface & LLMOps from working independently against the same internal model.

The existing [delivery RFC](../../../../../docs/delivery/RFC-MVP-Architecture.md) remains the evergreen architectural context. This RFC is the canonical temporal Phase 1 contract-lock artifact for `WS-001`, not the evergreen source of truth for the system as a whole.

## 2. MVP Invariants Carried Into Contract Lock

The following invariants are carried forward from the MVP and post-MVP framing docs and constrain all contracts in this RFC:

- Every uploaded document has a stable internal identity.
- Structural recovery may be partial, but provenance must not be fabricated.
- Every retrieval-addressable unit must be traceable to a source document and source location when available.
- Answer generation must remain grounded in retrieved corpus evidence.
- Insufficient evidence is a valid outcome and must be represented honestly.
- Mixed PDF and Markdown inputs must converge into one internal corpus model.
- Deferred MVP exclusions such as OCR, complex layout understanding, and advanced retrieval tuning must not become implicit prerequisites.

## 3. Phase 1 Required Outputs

This RFC and the adjacent schema package are intended to satisfy the required Phase 1 outputs from the framing workflow:

- a shared schema definition for core entities
- a documented contract for answer payloads and source references
- a documented lifecycle for document ingestion and processing
- a clear boundary map across Data Platform & Ingestion, Parsing & Structural Normalization, Search & Grounded Generation, and Product Surface & LLMOps
- initial contract tests and schema validation hooks

## 4. Shared Object Model

The contract layer is internal to the package and is not part of the stable public `parity` API surface.

### 4.1 Document

`Document` is the stable top-level identity for an uploaded source artifact.

Required fields:

- `doc_id`
- `workspace_id`
- `source_type` with allowed values `pdf` and `markdown`
- `title`
- `filename`
- `uploaded_at`
- `ingest_status`
- `storage_ref`

Optional fields:

- `metadata`

### 4.2 Section

`Section` represents a logical structural node recovered from source content.

Required fields:

- `section_id`
- `doc_id`
- `heading_path`
- `depth`

Optional fields:

- `parent_section_id`
- `heading_text`
- `page_start`
- `page_end`
- `source_start_offset`
- `source_end_offset`
- `structure_confidence`

### 4.3 Chunk / Retrieval Unit

`Chunk` is the retrieval-addressable text unit used by Search & Grounded Generation. The workflow sometimes refers to this concept as a retrieval unit; this RFC uses `Chunk` as the concrete internal model name for the repo.

Required fields:

- `chunk_id`
- `doc_id`
- `text`
- `ordinal`
- `heading_path`

Optional fields:

- `section_id`
- `page_start`
- `page_end`
- `source_start_offset`
- `source_end_offset`
- `lineage`
- `debug_metadata`

`lineage` is the current internal hook for transformation lineage, such as parser version, extraction mode, or chunker version, when those details become available.

### 4.4 SourceReference

`SourceReference` is the citation primitive returned to the answer layer and user-facing provenance surfaces.

Required fields:

- `doc_id`
- `document_title`
- `snippet`

Optional fields:

- `section_id`
- `heading_path`
- `page_label`
- `chunk_id`
- `passage_anchor`

`snippet` is the locked minimum inspectable provenance payload for Phase 1. `passage_anchor` is optional and additive.

`SourceReference` is allowed to omit heading and page details when the parser cannot recover them. It must always retain document identity, and it must not imply unsupported precision. Phase 1 therefore locks the minimum valid degraded citation shape as `doc_id + document_title + snippet`.

### 4.5 RetrievalHit

`RetrievalHit` represents a retrieval result forwarded into evidence packaging.

Required fields:

- `chunk_id`
- `doc_id`
- `score`
- `source_reference`

### 4.6 Answer

`Answer` represents the answer payload returned by the future answering layer.

Required fields:

- `status`
- `answer_text`
- `source_references`

Optional fields:

- `insufficiency_note`

Phase 1 implementation in `WS-001` locks only two answer statuses:

- `supported`
- `insufficient_evidence`

`supported` answers must include at least one `SourceReference`.

`supported` answers must not include an `insufficiency_note`.

`insufficient_evidence` answers must include a human-readable `insufficiency_note` and must carry `source_references=[]`. Phase 1 does not allow non-empty citations for `insufficient_evidence`, because the contract should not imply positive support where the system is explicitly declaring insufficient evidence.

This is an intentional Phase 1 simplification for the current workstream. The broader delivery docs still allow `partial` as an optional later status, but `WS-001` does not require it to unblock concurrent MVP implementation.

## 5. Lifecycle Semantics

Phase 1 locks the document processing lifecycle as a linear progression toward `ready`, with `failed` allowed from any in-progress state.

Locked status set:

- `uploaded`
- `registered`
- `extracting`
- `normalized`
- `chunked`
- `indexed`
- `ready`
- `failed`

Locked transition policy:

- `uploaded -> registered`
- `registered -> extracting`
- `extracting -> normalized`
- `normalized -> chunked`
- `chunked -> indexed`
- `indexed -> ready`
- any non-terminal in-progress state may transition to `failed`
- `ready` and `failed` are terminal

This RFC locks status semantics only. It does not lock orchestration technology, job transport, retry policy, or scheduling implementation.

## 6. Source-Reference And Answer-Status Contract

The source-reference and answer contracts are shared across Search & Grounded Generation, Product Surface & LLMOps, and any later source-inspection surface.

Contract rules:

- Citations are mandatory for `supported` answers.
- Citations must resolve to at least document identity and document title.
- Citations must include a snippet for direct inspection in Phase 1.
- Citations should include section or heading path when available.
- Citations should include a page reference when available.
- Citations may include a passage anchor in addition to the required snippet.
- Citation precision is allowed to degrade gracefully from document plus heading plus page to document-only provenance when needed.
- The system may expose partial structure, but it must not invent page numbers, headings, or section ownership.
- `insufficient_evidence` is a first-class answer outcome, not an exceptional failure path.
- `answer_text` remains required in both statuses so the product can return a usable user-facing response even when evidence is weak.
- `insufficient_evidence` responses must use an explicit empty citation list rather than fabricated support references.

## 7. Observability And Debug Contract

Phase 1 also locks the minimum shared debug visibility required for regression analysis and cross-domain tuning. This is not a production observability spec.

Minimum required shared visibility:

- what document was processed
- which parser path ran
- how sections were produced
- how many chunks were created
- what chunks were retrieved for a question
- what source units were handed to the answer generator
- what answer status was returned

## 8. Four-Domain Ownership Map

### 8.1 Data Platform & Ingestion

Owns upload entrypoints, document registration, raw storage references, processing orchestration, and readiness-state exposure.

### 8.2 Parsing & Structural Normalization

Owns text extraction from supported source files, hierarchy recovery, section construction, and conservative source-location recovery.

### 8.3 Search & Grounded Generation

Owns chunk generation, indexing inputs, retrieval selection, and evidence packaging into retrieval hits and source references.

### 8.4 Product Surface & LLMOps

Owns question/answer surface contract requirements, answer-status behavior, answer rendering requirements, provenance verification and source-inspection requirements, prompt strategy, and enforcement of grounded-answer semantics against the locked answer contract.

The four-domain model remains the ownership frame even if one engineer temporarily implements more than one domain.

## 9. Compatibility And Change Policy

- Treat these contracts as internal but shared. Domain work should code against them rather than redefining local variants.
- Prefer additive changes to fields and metadata.
- Renaming or removing required fields is a breaking contract change.
- Adding a new answer status is a breaking Phase 1 contract change unless WS-001 explicitly revises the RFC and tests.
- Changing processing-state semantics or allowed transitions is a breaking contract change.
- Do not promote this workstream RFC itself into the stable public package API.
- If these contracts become durable architectural truth beyond `WS-001`, they should be folded into the appropriate evergreen artifacts rather than leaving a temporal workstream RFC as the long-term source of truth.

## 10. Explicit Deferrals To Phase 2 And Later

The following areas are intentionally deferred beyond WS-001:

- public upload, query, and source-inspection API design
- parser heuristics for PDF heading inference and Markdown normalization
- chunk sizing, overlap, reranking, and context-assembly tuning
- prompt wording and answer-style optimization
- Golden Dataset scope, labeling, and evaluation harness design
- release-gate policy and release-evidence templates
- production observability, retries, and operational hardening
