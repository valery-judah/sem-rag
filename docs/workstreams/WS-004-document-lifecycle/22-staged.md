# Document Lifecycle Architecture for MVP

## Status

Draft

## Purpose

Define the implementation design for the MVP document lifecycle as a local-deployable Python service.

This document translates the existing lifecycle seam and MVP constraints into a concrete runtime design. It is intentionally limited to the document-ingestion and retrieval-preparation lifecycle. It does not define the query or answer-generation architecture.

## Scope alignment

This design is constrained by the current MVP framing and lifecycle requirements.

### Inputs

Supported source types:

* text-based PDF
* Markdown

Unsupported inputs must fail explicitly:

* scanned PDFs requiring OCR
* image-centric documents
* rich layout-dependent parsing
* tables, figures, diagrams, and pictures as first-class structures

### Lifecycle seam

The implementation must preserve the current internal lifecycle semantics:

`UPLOADED -> REGISTERED -> EXTRACTING -> NORMALIZED -> CHUNKED -> INDEXED -> READY`

`FAILED` is the terminal failure state reachable from any in-flight stage.

### Required trust properties

The design must preserve these properties:

* stable document identity
* recoverable structure and section hierarchy where possible
* provenance-bearing sections and chunks
* coarse but real traceability for PDFs
* honest failure behavior
* `READY` means retrievable and inspectable, not merely processed

## Design goals

1. Make the lifecycle real without broadening MVP scope.
2. Keep the runtime locally deployable with minimal infrastructure.
3. Preserve explicit stage boundaries for validation, retries, and inspection.
4. Persist evidence-bearing artifacts at each important stage.
5. Keep the design swappable so later cloud or distributed deployment does not force a domain rewrite.

## Non-goals

This design does not commit to:

* a public stable API
* a user-facing source inspection UI
* OCR or deep PDF layout understanding
* version-history, supersession, or withdrawal workflows
* connectors, sync, automation, or collaboration
* production-scale observability or multi-tenant control planes

---

# 1. System overview

## 1.1 Local deployment model

For MVP, the recommended deployment model is a single local service codebase with a small number of runtime components:

* HTTP service for intake and inspection
* background worker loop for stage execution
* SQL database for metadata and lifecycle truth
* local filesystem artifact store for raw and intermediate artifacts
* local vector index adapter for chunk publication

This is intentionally a single-node design. Stage separation exists in the code and persistence model, not in separate infrastructure tiers.

## 1.2 Runtime topology

```text
+----------------------------------------------------------+
| Local node                                                |
|                                                           |
|  +-------------------+      +--------------------------+  |
|  | HTTP/API service  | ---> | DocumentLifecycleService |  |
|  +-------------------+      +--------------------------+  |
|                                      |                    |
|                                      v                    |
|                           +-----------------------+       |
|                           | DB-backed job queue   |       |
|                           +-----------------------+       |
|                                      |                    |
|                                      v                    |
|                           +-----------------------+       |
|                           | Stage runner worker   |       |
|                           +-----------------------+       |
|                               |        |        |         |
|                               v        v        v         |
|                         +--------+ +--------+ +--------+  |
|                         | SQL DB | | Files  | | Vector |  |
|                         +--------+ +--------+ +--------+  |
+----------------------------------------------------------+
```

## 1.3 Why this shape

This shape is appropriate for MVP because it:

* preserves explicit lifecycle checkpoints
* makes failures inspectable
* supports retries without external orchestration infrastructure
* keeps local deployment simple
* avoids collapsing stage semantics into a single opaque ingest function

---

# 2. Architectural principles

## 2.1 Lifecycle state is the source of truth

The current document status is not decorative metadata. It is the authoritative statement of what artifacts are expected to exist and what operations are allowed.

## 2.2 Stage boundaries must correspond to persisted evidence

A stage should not be marked complete unless the artifact or invariant associated with that stage exists durably.

Examples:

* `NORMALIZED` means a persisted normalized artifact exists.
* `CHUNKED` means persisted `Section` and `Chunk` records exist.
* `INDEXED` means chunk publication records exist in the retrieval layer.
* `READY` means readiness checks over persisted artifacts pass.

## 2.3 Prefer conservative structure over fabricated structure

For Markdown, structure may be treated as strong when syntactically clear. For PDF, structure recovery should be useful but conservative. The system must not claim precise hierarchy or layout knowledge that it did not recover.

## 2.4 Provenance must be recoverable, even if coarse

For MVP, provenance does not need exact text-span anchors. It does need enough information to trace sections and chunks back to a document and a coarse location such as heading path, page range, section identity, or source offsets.

## 2.5 Stage execution must be idempotent at document scope

A stage should be safe to retry when practical. Re-running a non-terminal step must not create ambiguous ownership, duplicate child records, or broken cross-links.

## 2.6 Internal contracts matter more than transport contracts

The core design should center around internal models, repositories, stage interfaces, and invariants. HTTP routes and CLI commands are thin entry points and are not the architectural center of gravity.

---

# 3. Lifecycle state machine

## 3.1 States

```python
from enum import Enum

class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    REGISTERED = "REGISTERED"
    EXTRACTING = "EXTRACTING"
    NORMALIZED = "NORMALIZED"
    CHUNKED = "CHUNKED"
    INDEXED = "INDEXED"
    READY = "READY"
    FAILED = "FAILED"
```

## 3.2 State semantics

### `UPLOADED`

The raw file has been accepted and stored, but no durable document record beyond intake context is assumed.

### `REGISTERED`

A durable document record exists with stable identity and raw artifact linkage.

### `EXTRACTING`

Source-specific text extraction is in progress or has been entered as the active stage.

### `NORMALIZED`

A canonical normalized representation exists and is inspectable.

### `CHUNKED`

Persisted `Section` and `Chunk` records exist and satisfy integrity checks.

### `INDEXED`

Chunks have been published to the retrieval backend and publication records exist.

### `READY`

The document is retrievable and inspectable enough for MVP. This requires artifact and linkage checks, not merely successful execution flow.

### `FAILED`

The current ingest attempt terminated with an attributable failure.

## 3.3 Legal transitions

```text
UPLOADED   -> REGISTERED
REGISTERED -> EXTRACTING
EXTRACTING -> NORMALIZED
NORMALIZED -> CHUNKED
CHUNKED    -> INDEXED
INDEXED    -> READY

REGISTERED -> FAILED
EXTRACTING -> FAILED
NORMALIZED -> FAILED
CHUNKED    -> FAILED
INDEXED    -> FAILED
```

## 3.4 Retry model

For MVP, retries are document-scoped and stage-aware. A retry re-enters the failed or incomplete stage and may replace downstream child artifacts for that document.

The system does not yet model supersession, re-ingestion history, or multi-version lineage as first-class product concepts.

---

# 4. Domain model

## 4.1 Core entities

The domain is organized around a small number of durable entities.

### Document

Root identity and lifecycle owner.

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

@dataclass
class Document:
    doc_id: str
    workspace_id: str
    source_type: Literal["pdf", "markdown"]
    title: str
    filename: str
    checksum: str
    uploaded_at: datetime
    raw_storage_path: str
    status: DocumentStatus
    current_job_id: Optional[str] = None
    failure_code: Optional[str] = None
    failure_detail: Optional[str] = None
```

### LifecycleEvent

Append-only audit trail for transitions and stage outcomes.

```python
@dataclass
class LifecycleEvent:
    event_id: str
    doc_id: str
    stage: str
    from_status: str | None
    to_status: str
    occurred_at: datetime
    detail: dict
```

### ExtractedArtifact

Format-oriented intermediate output produced by extraction.

```python
@dataclass
class ExtractedArtifact:
    doc_id: str
    extractor_version: str
    source_type: str
    payload_path: str
    meta: dict
```

### NormalizedDocument

Canonical representation used by sectioning and chunking.

```python
@dataclass
class NormalizedDocument:
    doc_id: str
    normalizer_version: str
    payload_path: str
    stats: dict
```

### Section

Recoverable document structure unit.

```python
@dataclass
class Section:
    section_id: str
    doc_id: str
    parent_section_id: str | None
    heading_path: list[str]
    heading_text: str
    ordinal: int
    page_start: int | None
    page_end: int | None
    block_start: int
    block_end: int
    source_offset_start: int | None
    source_offset_end: int | None
```

### Chunk

Retrieval-addressable unit.

```python
@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    section_id: str
    ordinal: int
    heading_path: list[str]
    text: str
    token_count: int
    page_start: int | None
    page_end: int | None
    block_start: int
    block_end: int
    source_offset_start: int | None
    source_offset_end: int | None
```

### IndexEntry

Publication record proving the chunk exists in the retrieval backend.

```python
@dataclass
class IndexEntry:
    chunk_id: str
    doc_id: str
    index_backend: str
    index_key: str
    index_version: str
    published_at: datetime
```

### DocumentJob

Queued execution record for stage processing.

```python
@dataclass
class DocumentJob:
    job_id: str
    doc_id: str
    target_stage: str
    status: str
    attempt_count: int
    not_before: datetime | None
    error_code: str | None
    error_detail: str | None
```

## 4.2 Normalized representation

Normalization should produce an explicit intermediate artifact rather than an ephemeral in-memory structure only.

This design locks that choice for MVP.

### Why this is necessary

* it gives `NORMALIZED` a concrete meaning
* it supports inspection and debugging
* it enables stage-specific retries
* it isolates extraction concerns from sectioning/chunking concerns
* it makes regression testing easier

### Suggested normalized schema

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class NormalizedBlock:
    block_id: str
    kind: Literal[
        "heading",
        "paragraph",
        "list_item",
        "code",
        "table_like",
        "page_break",
        "quote",
        "unknown",
    ]
    text: str
    order_index: int
    heading_level: int | None
    page_start: int | None
    page_end: int | None
    source_offset_start: int | None
    source_offset_end: int | None
    meta: dict
```

```python
@dataclass
class NormalizedPayload:
    doc_id: str
    source_type: str
    blocks: list[NormalizedBlock]
    stats: dict
```

### Normalized artifact invariants

* preserves document order
* preserves or derives structure cues where recoverable
* carries provenance hooks when available
* never claims rich layout semantics not actually recovered

---

# 5. Stage-by-stage runtime design

## 5.1 Stage 0: Upload intake

### Responsibilities

* accept uploaded file
* validate extension and basic type
* store raw artifact to local filesystem
* compute checksum
* create initial upload context
* enqueue registration job

### Output

* raw file exists in artifact store
* upload metadata exists
* next stage is queued

### Failure conditions

* unsupported file type
* unreadable upload stream
* storage write failure

### Notes

Unsupported inputs must fail explicitly. The service should not attempt best-effort processing for scanned PDFs or unsupported types.

---

## 5.2 Stage 1: Registration (`REGISTERED`)

### Responsibilities

* create durable `Document` record
* assign stable `doc_id`
* persist workspace boundary
* persist source type, title, filename, checksum, upload time, raw artifact reference
* append lifecycle event
* enqueue extraction job

### Exit invariant

A `Document` exists and all downstream artifacts can reference it.

### Registration policy

Registration is the first stage where document identity becomes durable. All later entities must resolve through `doc_id`.

---

## 5.3 Stage 2: Extraction (`EXTRACTING`)

### Responsibilities

Transform raw input into recoverable extracted text.

### Markdown extraction path

Requirements:

* preserve raw text faithfully enough to retain headings, lists, paragraphs, and code fences
* preserve order exactly
* record source offsets when practical

Implementation notes:

* treat Markdown as trusted text input
* avoid destructive cleanup here
* do not flatten code blocks into prose

### PDF extraction path

Requirements:

* extract text from the existing text layer only
* preserve page boundaries when available
* preserve block order as best as the extractor can support
* no OCR
* no figure understanding
* no rich layout reconstruction

Implementation notes:

* prefer an extractor that exposes page-level grouping
* preserve page number and any layout hints that can later help heading inference
* capture warnings when the PDF text layer is sparse, malformed, or obviously low quality

### Extracted artifact shape

Suggested JSON shape:

```json
{
  "doc_id": "doc_123",
  "source_type": "pdf",
  "extractor_version": "v1",
  "pages": [
    {
      "page_number": 1,
      "blocks": [
        {"text": "1 Introduction", "order_index": 0, "meta": {}},
        {"text": "...", "order_index": 1, "meta": {}}
      ]
    }
  ],
  "meta": {
    "warnings": []
  }
}
```

### Failure conditions

* malformed PDF
* no recoverable text layer
* decode failure
* extractor exception

### Exit invariant

An inspectable extracted artifact exists and is attributable to the document.

---

## 5.4 Stage 3: Normalization (`NORMALIZED`)

### Responsibilities

Transform extracted content into a canonical structure-aware representation.

### Required outputs

The normalized representation must preserve or derive:

* document order
* headings and hierarchy when recoverable
* paragraphs and ordinary text boundaries
* code blocks and table-like text as plain text structures
* provenance hooks such as page ranges or source offsets when available

### Markdown normalization

Preferred behavior:

* parse Markdown structure conservatively
* recognize headings by syntax
* keep fenced code intact
* preserve list items distinctly
* preserve paragraph boundaries

### PDF normalization

Preferred behavior:

* preserve page transitions explicitly
* infer headings conservatively
* carry forward page-level provenance
* preserve line groups or paragraph groups in order

### Heading inference policy for PDFs

This design recommends conservative heuristics rather than deep layout reconstruction.

Possible heading signals:

* short isolated line shape
* numbering patterns like `1`, `1.2`, `2.3.1`
* extractor-supplied font size or style hints when available
* surrounding whitespace patterns
* repetition patterns consistent with section titles

A block should only be promoted to `heading` when confidence crosses a threshold. Otherwise it remains text.

### Synthetic structure fallback

When reliable headings are sparse in PDFs, the normalizer may preserve content as paragraph blocks and leave section derivation to create coarse synthetic sections later.

### Exit invariant

A persisted normalized artifact exists and can be inspected independently of extraction.

---

## 5.5 Stage 4: Section recovery and chunk production (`CHUNKED`)

### Responsibilities

* derive `Section` records from normalized content
* derive retrieval-ready `Chunk` records
* persist both
* verify cross-link integrity

## 5.5.1 Section derivation

### Markdown policy

Section tree is driven primarily by heading syntax.

### PDF policy

Section tree is driven by inferred headings when available. When not available, the system should create coarse but usable synthetic sections.

Examples:

* `Untitled section 01`
* `Page 12`
* `Pages 13-15`

Synthetic sections are acceptable if they still provide useful context and provenance.

### Section invariants

* every section belongs to exactly one document
* every section has a non-empty heading path
* parent-child relationships are reconstructible when the source supports them
* page range or offset metadata is attached when recoverable

## 5.5.2 Chunk derivation

### Chunking policy

Chunking should prefer discourse and section boundaries over naive fixed windows.

Recommended order of operations:

1. start from section-local content
2. group coherent adjacent paragraphs
3. keep code blocks intact where possible
4. avoid crossing major heading boundaries
5. only fall back to size-based splitting when content exceeds token limits

### Chunk size guidance

This design intentionally does not lock a single token budget as product policy. For MVP implementation, a target range such as 300 to 800 tokens with limited overlap is reasonable, but the boundary should remain configurable.

### Chunk metadata

Each chunk should carry:

* `doc_id`
* `section_id`
* `heading_path`
* `ordinal`
* page range when recoverable
* source offsets when recoverable
* normalized block span
* token count

### Integrity checks

Before marking `CHUNKED`, verify:

* every chunk references an existing section and document
* every section references an existing document
* no orphan chunks exist
* ordering is stable within document and section

### Exit invariant

Persisted `Section` and `Chunk` records exist and are internally consistent.

---

## 5.6 Stage 5: Publication (`INDEXED`)

### Responsibilities

* embed chunks
* publish them to the retrieval backend
* persist publication records
* validate publication completeness

### Design choice

Indexing should be a distinct stage boundary even if the same worker process performs it immediately after chunking.

### Why separate it

* gives publication its own retry boundary
* keeps `READY` semantically honest
* prevents chunked-but-unpublished documents from looking complete
* supports future evolution toward asynchronous indexing if needed

### Publication contract

For each chunk:

* compute embedding
* upsert into vector store
* persist `IndexEntry`

### Publication invariant

`INDEXED` is only valid if the expected number of publication records exists for the current chunk set.

### Retrieval backend abstraction

Use a narrow adapter interface so the backend can be swapped later.

```python
from typing import Protocol

class VectorIndex(Protocol):
    def upsert_chunk(self, *, chunk_id: str, text: str, metadata: dict) -> str:
        ...

    def delete_chunks_for_document(self, *, doc_id: str) -> None:
        ...

    def smoke_query(self, *, doc_id: str, text: str, k: int = 1) -> list[dict]:
        ...
```

---

## 5.7 Stage 6: Readiness (`READY`)

### Responsibilities

Validate that the document is both retrievable and inspectable enough for MVP.

### Readiness conditions

A document can transition to `READY` only if all of the following are true:

* the document record exists
* normalized structure exists
* sections exist
* chunks exist
* indexed retrieval artifacts exist
* chunk-to-section-to-document linkage is intact
* provenance meets minimum requirements
* retrieval smoke checks pass at least at a minimal level

### Minimum provenance rule

Each chunk must have:

* `doc_id`
* `heading_path`
* at least one coarse location reference from:

  * `section_id`
  * page range or page label
  * source offsets

### Recommended readiness predicate

```python
def is_ready(doc_id: str) -> bool:
    return (
        document_exists(doc_id)
        and normalized_exists(doc_id)
        and section_count(doc_id) > 0
        and chunk_count(doc_id) > 0
        and index_count(doc_id) == chunk_count(doc_id)
        and all_chunks_have_valid_owner_links(doc_id)
        and all_chunks_have_minimum_provenance(doc_id)
        and retrieval_smoke_passes(doc_id)
        and not has_open_failure(doc_id)
    )
```

### Retrieval smoke policy

For MVP, use a simple smoke check rather than full retrieval evaluation. Example:

* select one or more representative chunks from the document
* query the vector index with content sampled from those chunks
* verify the backend returns at least one result referencing that document

---

## 5.8 Failure handling (`FAILED`)

### Responsibilities

When a stage fails, preserve enough evidence to diagnose the failure without allowing partial artifacts to masquerade as ready content.

### Failure payload

At minimum preserve:

* document identity
* last attempted stage
* prior status
* failure transition
* error category or code
* operator-usable detail message
* partial artifact references if already written

### Failure categories

Recommended categories:

* `UNSUPPORTED_INPUT`
* `RAW_STORAGE_FAILURE`
* `REGISTRATION_FAILURE`
* `EXTRACTION_FAILURE`
* `NORMALIZATION_FAILURE`
* `SECTIONING_FAILURE`
* `CHUNKING_FAILURE`
* `INDEX_PUBLICATION_FAILURE`
* `READINESS_VALIDATION_FAILURE`
* `INTEGRITY_FAILURE`
* `INTERNAL_ERROR`

### Partial artifact policy

Do not automatically delete partial artifacts on failure. Preserve them for inspection, but exclude them from `READY` semantics.

---

# 6. Execution model

## 6.1 Orchestration approach

For MVP, use a DB-backed job queue with worker polling rather than an external broker such as Redis or RabbitMQ.

## 6.2 Why DB-backed jobs are sufficient now

* lower operational complexity
* easy local deployment
* transactional coordination with document state
* explicit retry and backoff support
* enough throughput for expected MVP corpus sizes

## 6.3 Job lifecycle

A job record tracks the stage to be executed and its attempt state.

Possible statuses:

* `queued`
* `running`
* `succeeded`
* `failed`
* `cancelled`

## 6.4 Worker loop sketch

```python
class LifecycleWorker:
    def run_forever(self) -> None:
        while True:
            job = self.jobs.claim_next()
            if not job:
                sleep(1.0)
                continue

            try:
                self.dispatch(job)
                self.jobs.mark_succeeded(job.job_id)
            except RetryableStageError as e:
                self.jobs.reschedule(job.job_id, error=e)
            except Exception as e:
                self.fail_document(job, e)
```

## 6.5 Stage runner contract

```python
from typing import Protocol

class StageRunner(Protocol):
    stage_name: str

    def run(self, *, doc_id: str) -> None:
        ...
```

Each stage runner should:

* validate current document status
* perform only the work for its stage
* persist its artifact or child entities
* emit lifecycle events
* enqueue the next stage on success
* fail explicitly on invariant violations

## 6.6 Idempotency strategy

Stage execution should be document-scoped and replace-or-upsert oriented.

Examples:

* registration should not create a second document for the same active upload context
* normalization may overwrite the normalized artifact for the document
* sectioning/chunking should replace the prior section/chunk set for that document during a retry
* index publication should delete-or-replace prior entries for that document before publishing a new set

This avoids ambiguous ownership without introducing full historical lineage.

---

# 7. Persistence design

## 7.1 Persistence split

Use two persistence classes:

* SQL database for metadata, lifecycle state, linkage, and job records
* filesystem artifact store for raw, extracted, and normalized payloads

## 7.2 Why this split

* structured linkage and queries belong in SQL
* large intermediate artifacts are easier to inspect on disk
* local deployment remains simple
* backups and debugging are straightforward

## 7.3 Suggested SQL tables

### `documents`

Columns:

* `doc_id` PK
* `workspace_id`
* `source_type`
* `title`
* `filename`
* `checksum`
* `uploaded_at`
* `raw_storage_path`
* `status`
* `failure_code`
* `failure_detail`
* `created_at`
* `updated_at`

### `lifecycle_events`

Columns:

* `event_id` PK
* `doc_id` FK
* `stage`
* `from_status`
* `to_status`
* `occurred_at`
* `detail_json`

### `document_jobs`

Columns:

* `job_id` PK
* `doc_id` FK
* `target_stage`
* `status`
* `attempt_count`
* `not_before`
* `error_code`
* `error_detail`
* `created_at`
* `updated_at`

### `sections`

Columns:

* `section_id` PK
* `doc_id` FK
* `parent_section_id` nullable FK
* `heading_path_json`
* `heading_text`
* `ordinal`
* `page_start`
* `page_end`
* `block_start`
* `block_end`
* `source_offset_start`
* `source_offset_end`

### `chunks`

Columns:

* `chunk_id` PK
* `doc_id` FK
* `section_id` FK
* `ordinal`
* `heading_path_json`
* `text`
* `token_count`
* `page_start`
* `page_end`
* `block_start`
* `block_end`
* `source_offset_start`
* `source_offset_end`

### `index_entries`

Columns:

* `chunk_id` PK/FK
* `doc_id` FK
* `index_backend`
* `index_key`
* `index_version`
* `published_at`

## 7.4 Filesystem layout

```text
data/
  raw/{workspace_id}/{doc_id}/source.pdf
  raw/{workspace_id}/{doc_id}/source.md
  extracted/{workspace_id}/{doc_id}/extracted.json
  normalized/{workspace_id}/{doc_id}/normalized.json
  debug/{workspace_id}/{doc_id}/events.jsonl
```

## 7.5 Repository layer

Use explicit repository interfaces rather than letting stage logic write SQL directly.

```python
class DocumentRepository(Protocol):
    def create(self, document: Document) -> None: ...
    def get(self, doc_id: str) -> Document: ...
    def update_status(self, doc_id: str, status: DocumentStatus, **kwargs) -> None: ...
```

```python
class SectionRepository(Protocol):
    def replace_for_document(self, doc_id: str, sections: list[Section]) -> None: ...
    def list_for_document(self, doc_id: str) -> list[Section]: ...
```

```python
class ChunkRepository(Protocol):
    def replace_for_document(self, doc_id: str, chunks: list[Chunk]) -> None: ...
    def list_for_document(self, doc_id: str) -> list[Chunk]: ...
```

---

# 8. Service interfaces

## 8.1 Internal service boundaries

The architecture should center on a small number of internal services.

### `DocumentLifecycleService`

Coordinates intake, job creation, status changes, and readiness checks.

### `ArtifactStore`

Reads and writes raw, extracted, and normalized artifacts.

### `ExtractionService`

Dispatches to format-specific extractors.

### `NormalizationService`

Dispatches to format-specific normalizers.

### `StructureService`

Builds sections from normalized blocks.

### `ChunkingService`

Builds chunks from sections and normalized blocks.

### `IndexPublicationService`

Embeds and publishes chunks.

### `ReadinessService`

Evaluates the `READY` predicate.

## 8.2 Suggested class skeletons

```python
class DocumentLifecycleService:
    def upload_document(self, *, workspace_id: str, title: str | None, file) -> str:
        ...

    def retry_document(self, *, doc_id: str) -> None:
        ...

    def get_status(self, *, doc_id: str) -> DocumentStatus:
        ...
```

```python
class ExtractionService:
    def extract(self, *, doc: Document) -> ExtractedArtifact:
        ...
```

```python
class NormalizationService:
    def normalize(self, *, doc: Document, extracted: ExtractedArtifact) -> NormalizedPayload:
        ...
```

```python
class StructureService:
    def derive_sections(self, *, doc: Document, normalized: NormalizedPayload) -> list[Section]:
        ...
```

```python
class ChunkingService:
    def derive_chunks(
        self,
        *,
        doc: Document,
        normalized: NormalizedPayload,
        sections: list[Section],
    ) -> list[Chunk]:
        ...
```

```python
class IndexPublicationService:
    def publish(self, *, doc: Document, chunks: list[Chunk]) -> list[IndexEntry]:
        ...
```

```python
class ReadinessService:
    def evaluate(self, *, doc_id: str) -> bool:
        ...
```

## 8.3 HTTP surface

The requirements do not lock a public API contract. For MVP, an internal runtime/admin API is sufficient.

Suggested endpoints:

* `POST /documents`
* `GET /documents/{doc_id}`
* `GET /documents/{doc_id}/status`
* `GET /documents/{doc_id}/artifacts`
* `POST /documents/{doc_id}/retry`
* `GET /workspaces/{workspace_id}/documents`
* `GET /healthz`
* `GET /readyz`

These endpoints are implementation conveniences, not product contracts.

---

# 9. Detailed behavior by source type

## 9.1 Markdown behavior

Markdown should be the strongest input path in MVP because it is already structured text.

### Expectations

* heading hierarchy is derived from syntax
* paragraph boundaries are reliable
* code fences are preserved
* lists are recoverable
* offsets can be tracked with relatively high confidence

### Risks

* malformed Markdown
* inconsistent heading level use
* mixed prose and pseudo-table formatting

## 9.2 PDF behavior

PDF should be treated as a text extraction problem with conservative structure recovery.

### Expectations

* page boundaries are usually recoverable
* heading inference is best-effort
* paragraph grouping may be imperfect
* provenance is often page-oriented and coarse

### Risks

* broken text layer
* line-wrap artifacts
* multi-column ordering issues
* repeated headers/footers contaminating blocks
* low-confidence heading recovery

### Mitigations

* preserve pages explicitly
* keep extraction warnings
* remove repeated boilerplate in normalization only when confidence is high
* allow synthetic sections when structure is weak

---

# 10. Integrity and invariants

## 10.1 Ownership invariants

* every `Section` must reference exactly one `Document`
* every `Chunk` must reference exactly one `Document`
* every `Chunk` must reference exactly one `Section`
* no `Chunk` may exist without its owning `Section`

## 10.2 Order invariants

* sections preserve document order
* chunks preserve section-local and document-global order
* normalized blocks preserve original reading order as best recovered

## 10.3 Provenance invariants

* each section has a non-empty heading path
* each chunk has a non-empty heading path
* each chunk has at least one coarse location reference
* PDF provenance may be coarse but cannot be absent

## 10.4 Readiness invariants

A document marked `READY` must have:

* a persisted normalized artifact
* persisted sections
* persisted chunks
* persisted index publication entries
* intact linkage across those records

## 10.5 Failure invariants

* failed documents are not treated as ready
* failures preserve operator-usable reason details
* partial artifacts do not count toward readiness unless the full stage invariant passes

---

# 11. Validation and testing strategy

## 11.1 Testing philosophy

Tests should validate lifecycle semantics and persisted artifacts, not only unit-level implementation details.

## 11.2 Contract tests

Validate:

* legal and illegal state transitions
* `FAILED` reachability from all in-flight stages
* readiness cannot be achieved without required artifacts
* core model invariants

## 11.3 Pipeline tests

Use representative fixtures to prove end-to-end behavior.

Required cases:

* Markdown fixture reaches `READY`
* text-based PDF fixture reaches `READY`
* malformed PDF reaches `FAILED`
* unsupported type is rejected explicitly

## 11.4 Persistence tests

Validate:

* document/section/chunk linkage integrity
* no orphan sections or chunks
* replace-on-retry behavior does not duplicate ownership
* index entries match active chunk set

## 11.5 Artifact tests

Validate:

* normalized artifact preserves order
* Markdown headings become expected section hierarchy
* PDF page anchors are preserved when recoverable
* coarse provenance exists for all ready chunks

## 11.6 Smoke retrieval tests

Validate:

* indexed chunks are queryable
* a query against representative chunk text returns at least one hit referencing the document

---

# 12. Observability for local MVP

This workstream does not require production-grade observability, but a minimum local debugging surface is still necessary.

## 12.1 Structured logs

Emit structured logs for:

* document upload
* stage start/finish
* transition events
* failures
* retry attempts
* readiness evaluation results

## 12.2 Operator inspection endpoints

Useful internal views:

* document status and failure info
* normalized artifact summary
* section and chunk counts
* index publication counts
* last N lifecycle events

## 12.3 Metrics

Optional but useful local counters:

* documents ingested
* documents ready
* failures by stage
* stage duration histograms
* retry counts

---

# 13. Security and trust boundary for local deployment

For MVP local deployment, security is intentionally simple.

## 13.1 Assumptions

* service runs in a trusted local or developer-controlled environment
* workspace ownership is a lightweight logical boundary, not a hardened multi-tenant security layer

## 13.2 Minimum precautions

* restrict artifact paths to managed directories
* validate filenames and avoid path traversal
* never trust upload metadata alone for source type
* cap file size and parsing timeouts reasonably

---

# 14. Repository and package layout

Suggested Python package layout:

```text
src/parity/
  app/
    api.py
    deps.py
    settings.py

  lifecycle/
    service.py
    orchestrator.py
    state_machine.py
    readiness.py
    errors.py

  stages/
    register.py
    extract.py
    normalize.py
    sectionize.py
    chunk.py
    index.py
    ready.py

  extractors/
    base.py
    markdown.py
    pdf.py

  normalizers/
    base.py
    markdown.py
    pdf.py

  structure/
    sections.py
    headings.py

  chunking/
    policy.py
    service.py
    tokens.py

  indexing/
    base.py
    embeddings.py
    vector_store.py

  persistence/
    models.py
    repositories.py
    jobs.py
    migrations/

  artifacts/
    schemas.py
    store.py

  domain/
    document.py
    section.py
    chunk.py
    provenance.py

  tests/
    contract/
    pipeline/
    persistence/
    fixtures/
```

### Design intent by package

* `domain/`: stable internal concepts and invariants
* `lifecycle/`: orchestration and state semantics
* `stages/`: concrete stage runners and stage-local logic
* `extractors/` and `normalizers/`: source-specific processing
* `structure/` and `chunking/`: structural recovery and retrieval-unit creation
* `indexing/`: embedding and publication adapters
* `persistence/`: storage implementations and migrations
* `artifacts/`: raw and intermediate payload handling

---

# 15. Recommended implementation sequence

## Phase 1: Registration and orchestration skeleton

Deliver:

* upload intake
* document registration
* job table and worker loop
* lifecycle transitions and failure recording
* placeholder downstream stage runners

Exit:

* a supported upload becomes a registered document with real state progression and inspectable failures

## Phase 2: Extraction and normalization

Deliver:

* Markdown extraction
* PDF text extraction
* persisted extracted artifact
* persisted normalized artifact
* explicit extraction/normalization failure paths

Exit:

* representative PDF and Markdown fixtures can reach `NORMALIZED`

## Phase 3: Sectioning and chunking

Deliver:

* section derivation
* chunk derivation
* persistence and integrity checks
* replace-on-retry behavior

Exit:

* representative fixtures can reach `CHUNKED`

## Phase 4: Index publication and readiness

Deliver:

* embedding and vector publication
* index entry persistence
* readiness predicate
* retrieval smoke test coverage

Exit:

* representative fixtures can reach `READY`

---

# 16. Decision log

## Decision 1: Persist normalized artifacts explicitly

Accepted.

Rationale:

* needed for inspectability
* gives `NORMALIZED` real semantics
* improves retry/debugging/testability

## Decision 2: Keep indexing as a separate lifecycle stage

Accepted.

Rationale:

* preserves honest readiness semantics
* introduces a clean retry boundary
* prevents chunked-only documents from appearing complete

## Decision 3: Use conservative PDF heading inference

Accepted.

Rationale:

* aligned with MVP scope
* avoids false structural claims
* coarse synthetic sections remain allowed fallback

## Decision 4: Use DB-backed jobs for local MVP

Accepted.

Rationale:

* minimal local operational complexity
* enough reliability for staged lifecycle processing
* easy migration path to external workers later

## Decision 5: Split SQL metadata from filesystem artifacts

Accepted.

Rationale:

* keeps artifacts inspectable
* keeps linkage queryable
* simple local deployment

---

# 17. Open issues intentionally deferred

These questions are intentionally left outside the MVP lifecycle design:

* public API stabilization
* re-ingestion and supersession semantics
* exact citation anchor model beyond coarse provenance
* hybrid retrieval strategy
* sophisticated PDF layout analysis
* document withdrawal or garbage collection policy
* scaling beyond a single-node deployment

---

# 18. Implementation checklist

## Core

* [ ] implement `Document` and lifecycle persistence models
* [ ] implement job queue and worker
* [ ] implement lifecycle state validation
* [ ] implement upload intake and raw artifact storage

## Extraction and normalization

* [ ] implement Markdown extractor
* [ ] implement PDF extractor
* [ ] define extracted artifact schema
* [ ] define normalized artifact schema
* [ ] implement Markdown normalizer
* [ ] implement PDF normalizer with conservative heading inference

## Structure and chunks

* [ ] implement section derivation
* [ ] implement chunking policy
* [ ] persist sections and chunks with integrity checks

## Publication and readiness

* [ ] implement embedding adapter
* [ ] implement vector index adapter
* [ ] persist index entries
* [ ] implement readiness predicate
* [ ] implement retrieval smoke checks

## Validation

* [ ] contract tests
* [ ] pipeline tests for PDF and Markdown to `READY`
* [ ] failure-path tests
* [ ] persistence integrity tests

---

# 19. Bottom line

For MVP, the correct architecture is a single-node Python service with explicit lifecycle stage runners, DB-backed orchestration, persisted normalized artifacts, conservative PDF structure recovery, section-first chunking, separate index publication, and a strict readiness predicate tied to persisted provenance-bearing artifacts.

That is the smallest design that satisfies the lifecycle requirements without broadening the MVP scope.

---

# 20. Implementation plan as stacked PRs

## 20.1 Recommended execution unit

Use **stacked PRs** as the primary implementation unit.

Why this is the best fit here:

* the lifecycle requirements are staged already
* each stage has a clear semantic exit signal
* the coding agent will perform better with bounded, reviewable deltas
* failures are easier to localize when each PR introduces one new invariant layer
* the team can stop after any completed slice and still retain a coherent partial system

Avoid one large pipeline PR. It will be harder to review, harder to debug, and more likely to blur lifecycle semantics.

Also avoid ultra-small mechanical PRs that do not produce a meaningful seam. The coding agent tends to lose architectural intent when the unit of work is too fine-grained.

## 20.2 PR sizing rule

Each PR should satisfy all of the following:

* introduces one primary architectural seam or one lifecycle milestone
* leaves the repo in a runnable, testable state
* includes tests at the same semantic level as the added capability
* avoids introducing placeholder abstractions that are not exercised immediately
* stays narrow enough that a reviewer can understand the change in one sitting

A good target is **7 to 12 PRs** total for this workstream.

## 20.3 Review policy for the coding agent

For each PR, require the agent to include:

* purpose
* exact files expected to change
* invariants added or enforced
* tests added
* what is intentionally deferred to the next PR

This helps prevent accidental scope bleed into retrieval, answer generation, or public API design.

---

# 21. PR plan

## PR 0. Repo alignment and architecture guardrails

### Purpose

Create the minimal scaffolding needed so later PRs do not drift away from the locked lifecycle contract or MVP scope.

### Deliverables

* add or update the architecture doc with the lifecycle design
* add a short ADR or design note stating:

  * supported inputs are PDF and Markdown only
  * lifecycle seam is fixed
  * OCR and rich layout work are out of scope
  * `READY` requires persisted retrievable artifacts
* add a small module-level README or package notes for the lifecycle area

### Code shape

Likely files:

* `docs/evergreen/architecture.md` or equivalent repo doc
* `docs/adr/...` or `docs/design/...`
* optional package README under `src/parity/lifecycle/`

### Tests

None required beyond doc linting if present.

### Why first

This PR makes the agent operate against explicit constraints instead of inferring them from scattered docs.

---

## PR 1. Core domain and lifecycle contract enforcement

### Purpose

Make the lifecycle and core entity boundaries explicit in code before any real pipeline logic lands.

### Deliverables

* define or refine core models for:

  * `Document`
  * `DocumentStatus`
  * `LifecycleEvent`
  * stage/failure categories
* define legal lifecycle transitions
* implement lifecycle validation utilities
* add a single source of truth for status progression

### Code shape

Likely files:

* `src/parity/domain/document.py`
* `src/parity/lifecycle/state_machine.py`
* `src/parity/lifecycle/errors.py`
* align with existing contract modules under `src/parity/_contracts/...`

### Tests

* allowed transitions pass
* illegal transitions fail
* `FAILED` is reachable only from in-flight states as intended
* status semantics remain aligned with the existing seam

### Exit condition

The repo has an executable lifecycle contract independent of storage or pipeline execution.

### Why this granularity

This PR is small but foundational. It prevents later pipeline code from embedding inconsistent status behavior.

---

## PR 2. Persistence foundation and artifact store

### Purpose

Introduce the persistence primitives needed for all later stages without yet implementing extraction or chunking.

### Deliverables

* SQL models and migrations for:

  * `documents`
  * `lifecycle_events`
  * `document_jobs`
* artifact store abstraction for:

  * raw artifacts
  * extracted artifacts
  * normalized artifacts
* repository interfaces and initial implementations
* local filesystem layout for artifact storage

### Code shape

Likely files:

* `src/parity/persistence/models.py`
* `src/parity/persistence/repositories.py`
* `src/parity/persistence/migrations/...`
* `src/parity/artifacts/store.py`
* `src/parity/artifacts/schemas.py`

### Tests

* migration smoke test
* document repository round-trip tests
* artifact store write/read tests
* lifecycle event persistence tests

### Exit condition

The repo can persist documents, jobs, lifecycle events, and raw/intermediate artifacts locally.

### Why now

Registration and worker execution should land on real storage rather than mocks. That keeps later PRs vertical.

---

## PR 3. Intake path and registration stage

### Purpose

Make upload/registration real enough to create durable document records and raw artifact references.

### Deliverables

* upload intake service or internal command path
* supported type validation for PDF and Markdown only
* checksum generation
* raw artifact persistence
* document registration into `REGISTERED`
* lifecycle event creation
* explicit rejection of unsupported inputs

### Code shape

Likely files:

* `src/parity/lifecycle/service.py`
* `src/parity/stages/register.py`
* `src/parity/app/api.py` or internal CLI entrypoint

### Tests

* PDF upload registers successfully
* Markdown upload registers successfully
* unsupported type fails explicitly
* raw storage path is persisted
* lifecycle event trail is recorded

### Exit condition

An uploaded source becomes a durable `Document` with stable identity and persisted raw artifact linkage.

### Why this boundary

It satisfies the first meaningful business invariant: document identity survives later stages.

---

## PR 4. Job orchestration and worker skeleton

### Purpose

Make stage execution explicit and retryable before the real transformation stages arrive.

### Deliverables

* DB-backed job queue logic
* worker loop
* job claiming and status updates
* dispatch by stage name
* explicit failure capture and transition to `FAILED`
* placeholder stage runners only where necessary

### Code shape

Likely files:

* `src/parity/lifecycle/orchestrator.py`
* `src/parity/persistence/jobs.py`
* `src/parity/stages/base.py`
* `src/parity/lifecycle/worker.py`

### Tests

* queued job can be claimed and run
* stage failure records `FAILED`
* retryable vs terminal error handling behaves as expected
* worker does not skip lifecycle validation

### Exit condition

A registered document can move through explicit stage machinery with real failure accounting.

### Why separate from PR 3

Registration and orchestration are related but distinct. Keeping them separate reduces the blast radius when worker semantics change.

---

## PR 5. Extraction paths for Markdown and PDF

### Purpose

Implement recoverable extraction for the two supported input types.

### Deliverables

* Markdown extractor
* text-PDF extractor
* extracted artifact schema and persistence
* extraction warnings and explicit failure reporting
* page-aware extraction metadata for PDFs when available

### Code shape

Likely files:

* `src/parity/extractors/base.py`
* `src/parity/extractors/markdown.py`
* `src/parity/extractors/pdf.py`
* `src/parity/stages/extract.py`

### Tests

* Markdown fixture extracts with preserved text cues
* text-PDF fixture extracts with page-aware structure
* malformed PDF fails explicitly
* extracted artifacts are inspectable and attributable to the document

### Exit condition

Representative PDF and Markdown inputs can reach `EXTRACTING` and produce durable extracted artifacts.

### Why here

This is the first real content transformation seam and should be isolated from normalization logic for debugging clarity.

---

## PR 6. Normalization and normalized artifact persistence

### Purpose

Convert extracted content into the canonical intermediate representation that later stages consume.

### Deliverables

* normalized payload schema
* Markdown normalizer
* PDF normalizer
* conservative PDF heading inference policy
* preservation of order, paragraphs, code blocks, and provenance hooks where available
* persisted normalized artifact
* transition to `NORMALIZED`

### Code shape

Likely files:

* `src/parity/normalizers/base.py`
* `src/parity/normalizers/markdown.py`
* `src/parity/normalizers/pdf.py`
* `src/parity/stages/normalize.py`
* `src/parity/artifacts/schemas.py`

### Tests

* Markdown normalization produces expected heading and block structure
* PDF normalization preserves page/order information
* normalized artifacts are persisted and inspectable
* failure reporting is explicit when normalization cannot proceed

### Exit condition

Representative fixtures can reach `NORMALIZED` with real normalized output.

### Why keep separate from extraction

The requirements explicitly treat extraction and normalization as a joint delivery stage, but implementation should split them. This isolates source decoding problems from structure modeling problems while still satisfying the same stage goal.

---

## PR 7. Section recovery and section persistence

### Purpose

Turn normalized structure into stable `Section` records before chunking enters the picture.

### Deliverables

* section derivation service
* heading-path generation
* parent/child relationship reconstruction where supported
* coarse synthetic sections for weakly structured PDFs
* section persistence and replacement-on-retry semantics

### Code shape

Likely files:

* `src/parity/structure/sections.py`
* `src/parity/stages/sectionize.py`
* repository additions in persistence layer

### Tests

* every section belongs to one document
* heading paths are non-empty
* Markdown hierarchy reconstructs correctly for representative fixtures
* coarse PDF sections are still useful and attributable

### Exit condition

A normalized document can produce persisted, inspectable `Section` records with stable ownership.

### Why separate from chunking

Section recovery is a first-class invariant in the requirements. Keeping it isolated makes provenance and structure bugs much easier to diagnose.

---

## PR 8. Chunk production and integrity checks

### Purpose

Produce retrieval-addressable `Chunk` records with stable provenance and ordering.

### Deliverables

* chunking policy implementation
* section-first chunk derivation
* code-block preservation when practical
* token counting utility
* chunk persistence
* integrity checks across document, section, and chunk ownership
* transition to `CHUNKED`

### Code shape

Likely files:

* `src/parity/chunking/policy.py`
* `src/parity/chunking/service.py`
* `src/parity/stages/chunk.py`
* chunk repository additions

### Tests

* chunks preserve ownership and order
* heading-path context is attached
* chunking favors section/discourse boundaries over naive splits where available
* no orphan chunks exist
* representative fixtures reach `CHUNKED`

### Exit condition

Representative documents can reach `CHUNKED`, and sections/chunks are internally consistent and inspectable.

### Why this is its own PR

This is the first point where retrieval semantics start to matter. It deserves its own review.

---

## PR 9. Index publication adapter and `INDEXED` semantics

### Purpose

Publish chunks to the retrieval backend without yet expanding into broader query architecture.

### Deliverables

* embedding adapter interface
* vector index adapter interface and local implementation
* index publication service
* `IndexEntry` persistence
* replace-or-delete publication semantics for retries
* transition to `INDEXED`

### Code shape

Likely files:

* `src/parity/indexing/base.py`
* `src/parity/indexing/embeddings.py`
* `src/parity/indexing/vector_store.py`
* `src/parity/stages/index.py`

### Tests

* all chunks for a document can be published
* index entries are persisted and match the active chunk set
* re-publication does not create ambiguous ownership
* indexing failures transition cleanly to `FAILED`

### Exit condition

A `CHUNKED` document can be published into the retrieval layer and prove index presence through persisted entries.

### Why separate from chunking

The requirements explicitly state that `READY` must mean retrievable, not just chunked. This PR creates that boundary.

---

## PR 10. Readiness predicate and retrieval smoke coverage

### Purpose

Define the real meaning of `READY` and enforce it as code.

### Deliverables

* readiness evaluation service
* invariant checks over normalized artifact, sections, chunks, and index entries
* minimum provenance checks
* minimal retrieval smoke test path
* transition to `READY`

### Code shape

Likely files:

* `src/parity/lifecycle/readiness.py`
* `src/parity/stages/ready.py`
* small inspection endpoint or internal command for readiness details

### Tests

* document cannot become `READY` without indexed chunks
* document cannot become `READY` without provenance-bearing linkage
* retrieval smoke path passes for representative documents
* `FAILED` documents cannot masquerade as ready

### Exit condition

Representative PDF and Markdown fixtures can reach `READY` with real retrievability and inspectability guarantees.

### Why this deserves its own PR

This is the trust boundary for the whole lifecycle. It should be reviewed independently from indexing mechanics.

---

## PR 11. Retry semantics, replacement behavior, and failure hardening

### Purpose

Make the pipeline operationally safe for repeated execution on the same document without introducing full version-history semantics.

### Deliverables

* document-level retry entry point
* retry rules per stage
* replace-on-retry behavior for sections, chunks, and index entries
* clearer failure categories and operator-visible diagnostics
* explicit handling of partial artifact preservation

### Code shape

Likely files:

* `src/parity/lifecycle/service.py`
* `src/parity/lifecycle/errors.py`
* persistence repository methods for replacement behavior

### Tests

* retry after extraction failure works correctly
* retry after chunk/index failure does not duplicate ownership
* partial artifacts do not satisfy readiness
* failure details remain inspectable

### Exit condition

The staged pipeline supports safe retries at document scope for non-terminal failures.

### Why after readiness

Retry logic is easier to implement correctly after the happy path and invariants are fully defined.

---

## PR 12. End-to-end validation and developer ergonomics

### Purpose

Close the loop with test fixtures, commands, and minimal inspection surfaces that make the pipeline usable by engineers.

### Deliverables

* end-to-end pipeline tests from upload to `READY`
* representative PDF and Markdown fixtures committed or referenced in test data
* local dev commands for worker/service start
* basic health and readiness endpoints
* optional artifact inspection endpoint for debugging

### Code shape

Likely files:

* `tests/pipeline/...`
* `tests/fixtures/...`
* `src/parity/app/api.py`
* `Makefile` or task runner config
* `docker-compose.yml` if used now

### Tests

* full happy path for Markdown
* full happy path for text-PDF
* malformed or unsupported input failure paths
* persistence integrity checks at end-to-end level

### Exit condition

A developer can run the service locally, ingest representative fixtures, and observe documents reach `READY` through the full staged lifecycle.

### Why last

This PR should consolidate the end-to-end experience once the lifecycle semantics are already stable.

---

# 22. Alternative grouping when the team wants fewer PRs

If 12 PRs feels too fine-grained for your repo cadence, compress into **8 PRs** by merging these pairs:

* merge PR 0 and PR 1
* merge PR 2 and PR 3
* merge PR 5 and PR 6
* merge PR 7 and PR 8
* merge PR 9 and PR 10 only if the readiness predicate is still reviewed explicitly inside the PR description

Do **not** merge chunking and indexing into a single unreviewed blob. That tends to obscure the difference between “structured” and “retrievable.”

---

# 23. Recommended order for the coding agent

This is the exact order I recommend the agent execute:

1. PR 1 — lifecycle contract
2. PR 2 — persistence foundation
3. PR 3 — intake and registration
4. PR 4 — worker and orchestration
5. PR 5 — extraction
6. PR 6 — normalization
7. PR 7 — sections
8. PR 8 — chunks
9. PR 9 — indexing
10. PR 10 — readiness
11. PR 11 — retry and hardening
12. PR 12 — end-to-end dev ergonomics

PR 0 can happen first if the repo currently lacks an explicit architecture note. Otherwise treat it as already satisfied by this document.

---

# 24. Instructions for the coding agent per PR

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
Add tests at the same semantic level as the PR’s invariant.
At the end, summarize:
1. files changed,
2. invariants enforced,
3. tests added,
4. what remains for PR N+1.
```

---

# 25. Final recommendation

Use **stacked PRs** as the working unit.

For this repo, the most effective granularity is:

* small enough that each PR establishes one new invariant layer
* large enough that each PR leaves behind a runnable, reviewable vertical slice

If you want the highest signal path with the coding agent, start with PR 1 through PR 4 before touching extraction. That will force the runtime seams, persistence, and failure model to stabilize first, which reduces rework in the content-processing stages.
