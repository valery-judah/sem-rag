Below is a concrete v1 design for the **document lifecycle as a local-deployable Python service**, constrained to the lifecycle scope you already defined: text-based PDF and Markdown only, locked lifecycle seam preserved, coarse provenance allowed, and `READY` meaning retrievable plus inspectable rather than merely processed.  

## 1. Design target

Build a **single-node service** that accepts document uploads, runs them through:

`UPLOADED -> REGISTERED -> EXTRACTING -> NORMALIZED -> CHUNKED -> INDEXED -> READY`

and persists enough artifacts that later retrieval/query work can consume them without bypassing the lifecycle. This keeps the service aligned with the MVP framing: mixed-format corpus, lightweight structure recovery, grounded provenance, and explicit failure behavior.   

## 2. Recommended service shape

For MVP, use **one Python codebase, one deployable service image, one local database, one local file store, and one in-process/background worker loop**.

That gives you:

* minimal operational surface for local deployment
* explicit stage execution and retries
* persisted lifecycle truth
* no dependency on external brokers or cloud primitives

The important design choice is: **separate stage boundaries in code and persistence, but not necessarily separate infrastructure**. So `EXTRACTING`, `NORMALIZED`, `CHUNKED`, and `INDEXED` are distinct stage runners and persisted checkpoints, even if one worker executes them sequentially in the same process. That matches your lifecycle discipline and retry requirements without overbuilding orchestration.  

### Runtime topology

```text
+------------------------------------------------------+
| Local Deployable Service                             |
|                                                      |
|  +----------------+     +-------------------------+  |
|  | HTTP/API layer | --> | DocumentLifecycleSvc    |  |
|  +----------------+     +-------------------------+  |
|                              |                       |
|                              v                       |
|                    +----------------------+          |
|                    | Stage runners        |          |
|                    | register/extract/... |          |
|                    +----------------------+          |
|                              |                       |
|             +----------------+------------------+    |
|             |                                   |    |
|             v                                   v    |
|      +-------------+                    +-------------+
|      | SQL store   |                    | File store  |
|      | docs/jobs/  |                    | raw/extract |
|      | sections/...|                    | normalized  |
|      +-------------+                    +-------------+
|             |                                   |
|             +----------------+------------------+
|                              |
|                              v
|                      +----------------+
|                      | Vector index    |
|                      | local adapter   |
|                      +----------------+
+------------------------------------------------------+
```

## 3. Primary design decisions

### A. Treat lifecycle as the source of truth

The lifecycle is not a logging convenience. It is the state machine that determines what exists and whether a document is usable. `READY` should be computed only after artifact and linkage checks pass. 

### B. Persist an explicit normalized intermediate artifact

Use a real intermediate representation between extraction and section/chunk derivation.

This resolves one of the open questions cleanly: **normalization should produce an explicit persisted artifact**. Without it, extraction bugs, structure heuristics, and chunking regressions become hard to inspect and hard to retry independently. With it, `NORMALIZED` becomes a real semantic checkpoint rather than an implementation blur. That aligns with the requirement that normalized output be inspectable and provenance-bearing.  

### C. Prefer conservative PDF structure recovery

For Markdown, heading structure can be strong. For PDFs, do not overclaim hierarchy. Infer headings only when confidence is reasonable; otherwise fall back to coarse section buckets anchored by page ranges and document order. This respects the MVP rule that provenance may be coarse, but not absent.  

### D. Keep indexing as a separate stage boundary

Even if the same worker executes it inline, `INDEXED` should remain a distinct persisted state and retry boundary. This makes `READY` meaningful and prevents “chunked but not actually retrievable” documents from looking complete. 

## 4. Domain model

The service should revolve around a small set of persistent entities.

### Document

The root record. Durable identity starts here.

```python
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

```python
@dataclass
class Document:
    doc_id: str
    workspace_id: str
    source_type: Literal["pdf", "markdown"]
    title: str
    filename: str
    uploaded_at: datetime
    raw_storage_path: str
    status: DocumentStatus
    failure_code: str | None
    failure_detail: str | None
    checksum: str
```

### ExtractedArtifact

Raw extracted content, still format-oriented.

```python
@dataclass
class ExtractedArtifact:
    doc_id: str
    extractor_version: str
    pages: list["ExtractedPage"] | None        # for PDFs
    markdown_text: str | None                  # for Markdown
    extraction_meta: dict
```

### NormalizedDocument

Canonical structure for later stages.

```python
@dataclass
class NormalizedDocument:
    doc_id: str
    normalizer_version: str
    blocks: list["NormalizedBlock"]
    stats: dict
```

```python
@dataclass
class NormalizedBlock:
    block_id: str
    kind: Literal["heading", "paragraph", "list_item", "code", "table_like", "page_break"]
    text: str
    order_index: int
    heading_level: int | None
    page_start: int | None
    page_end: int | None
    source_offset_start: int | None
    source_offset_end: int | None
```

### Section

Recoverable document structure.

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
```

### Chunk

Retrieval unit.

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
    embedding_ref: str | None
```

### IndexEntry

Publication record that proves the chunk is retrievable.

```python
@dataclass
class IndexEntry:
    chunk_id: str
    doc_id: str
    index_backend: str
    index_key: str
    published_at: datetime
    index_version: str
```

### LifecycleEvent

Append-only operational record.

```python
@dataclass
class LifecycleEvent:
    event_id: str
    doc_id: str
    from_status: str | None
    to_status: str
    stage: str
    occurred_at: datetime
    detail: dict
```

## 5. Stage-by-stage design

### Stage 0: `UPLOADED`

Meaning: raw file accepted and stored, but not yet registered into durable lifecycle metadata.

What happens:

* validate file extension and basic MIME/type
* write raw artifact to local file storage
* compute checksum
* enqueue registration job

Failure mode:

* unsupported input rejected explicitly
* no transition beyond `UPLOADED` if storage fails

This follows the hard bound that only text-based PDFs and Markdown are supported. Unsupported inputs must fail explicitly. 

---

### Stage 1: `REGISTERED`

Meaning: a durable `Document` record exists.

What happens:

* create `Document`
* assign `doc_id`
* bind `workspace_id`
* persist title, filename, source type, uploaded timestamp, raw storage ref, status
* append lifecycle event

Invariant:

* every downstream artifact resolves back to `doc_id`

This directly satisfies stable document identity and workspace/corpus ownership requirements. 

---

### Stage 2: `EXTRACTING`

Meaning: source-specific extraction is running.

#### Markdown path

* read UTF-8 text
* preserve source faithfully
* keep line/order fidelity
* preserve code fences and headings as text

#### PDF path

* extract text in reading order as best available
* preserve page boundaries
* keep page-number association per extracted block
* do not attempt OCR
* do not attempt rich layout or figure understanding

Persist:

* one `ExtractedArtifact`
* page/block-level extraction metadata
* extraction warnings if quality is weak

Failure:

* malformed PDF
* unreadable text layer
* decode error for Markdown

This stays within MVP scope: text PDFs, no OCR, no rich layout reconstruction.  

---

### Stage 3: `NORMALIZED`

Meaning: extracted content has been converted into a canonical, structure-aware representation.

What normalization should do:

* preserve document order
* normalize whitespace
* classify blocks
* recognize Markdown headings exactly
* infer PDF headings heuristically and conservatively
* mark page transitions
* preserve coarse provenance hooks: page ranges, block order, offsets when available

Key rule:

* normalization must not pretend to know more structure than it actually recovered

Recommended heuristic policy for PDF heading inference:

* promote a line/block to heading only if signals exceed threshold
* signals can include font/style hints if extractor provides them, short-line shape, numbering patterns, surrounding whitespace, repeated TOC-like patterns
* if confidence is low, keep as paragraph text

That gives you useful section recovery without drifting into fake structure.  

---

### Stage 4: `CHUNKED`

Meaning: section recovery and retrieval-unit generation are complete.

#### Section derivation

Build a section tree from normalized blocks:

* Markdown: driven by heading levels
* PDF: driven by inferred headings; if sparse, create coarse synthetic sections such as `Page 12`, `Page 13–15`, or `Untitled section N`

Important detail:

* synthetic/coarse sections are acceptable for MVP
* they must still have non-empty heading paths

#### Chunking policy

Chunk from section content, not fixed windows first.

Order of preference:

1. paragraph groups within section
2. code block kept intact when possible
3. small adjacent paragraphs merged
4. fallback split only when size exceeds token limit

Chunk metadata must carry:

* `doc_id`
* `section_id`
* heading path
* ordinal
* page range
* block range / source offsets when present

This matches the requirement that chunking favor discourse and section boundaries over naive fixed windows. 

---

### Stage 5: `INDEXED`

Meaning: chunks were published to the retrieval layer.

What happens:

* embed each chunk
* upsert into vector index
* persist `IndexEntry`
* verify index count matches chunk count for current index version

Design rule:

* indexing is publication, not mere side effect
* if vector publication fails, the document does not become `READY`

This is where the retrieval contract begins to exist operationally. 

---

### Stage 6: `READY`

Meaning: the document is retrievable and inspectable enough for MVP.

`READY` check should verify:

* `Document` exists
* `NormalizedDocument` exists
* `Section` records exist
* `Chunk` records exist
* `IndexEntry` records exist
* all chunks resolve to a section and document
* provenance fields meet minimum threshold

This is the exact place to enforce “coarse provenance is acceptable; missing provenance is not.” 

---

### Failure path: `FAILED`

Failure should be terminal for the current run and operator-visible.

Persist at minimum:

* `doc_id`
* last reached status
* stage name
* failure category/code
* failure detail
* timestamps
* partial artifact references if already produced

Do not delete partial artifacts automatically. Keep them for inspection, but keep them unreachable from `READY` flows. That matches the requirement for honest failure behavior and operator-usable diagnostics. 

## 6. Orchestration model

For local MVP, use a **DB-backed work queue** rather than Celery/Redis.

### Why

* fewer moving parts
* retries can be modeled transactionally
* one local deployment remains practical
* stage runners remain explicit and swappable

### Job table

```python
@dataclass
class DocumentJob:
    job_id: str
    doc_id: str
    target_stage: Literal["REGISTER", "EXTRACT", "NORMALIZE", "CHUNK", "INDEX", "READY_CHECK"]
    status: Literal["queued", "running", "succeeded", "failed"]
    attempt_count: int
    not_before: datetime | None
    error_code: str | None
```

### Worker policy

* one or more worker loops poll queued jobs
* each stage runner is idempotent at document scope
* retries allowed for non-terminal execution failures
* stage handlers must check current document status before mutating state

This supports your retry requirement without introducing full document version-history semantics yet. 

## 7. Persistence layout

For a local deployable service, split persistence into **SQL metadata** and **filesystem artifacts**.

### SQL store

Use it for:

* documents
* lifecycle events
* jobs
* sections
* chunks
* index entries
* failures

### File store

Use it for:

* raw uploaded source
* extracted artifact JSON
* normalized artifact JSON

### Suggested layout

```text
data/
  raw/{workspace_id}/{doc_id}/source.pdf
  raw/{workspace_id}/{doc_id}/source.md
  extracted/{workspace_id}/{doc_id}/extracted.json
  normalized/{workspace_id}/{doc_id}/normalized.json
  logs/{workspace_id}/{doc_id}/events.jsonl
```

Reasoning:

* raw and intermediate artifacts are easier to inspect on disk
* relational entities and lifecycle truth belong in SQL
* this keeps operator debugging simple during local deployment

## 8. Internal API surface

Your requirements explicitly avoid committing to a stable public API, so the interface below should be treated as an **internal admin/runtime surface**, not a public contract. 

### Minimal endpoints

```text
POST   /documents
GET    /documents/{doc_id}
GET    /documents/{doc_id}/status
GET    /documents/{doc_id}/artifacts
POST   /documents/{doc_id}/retry
GET    /workspaces/{workspace_id}/documents
GET    /healthz
GET    /readyz
```

### `POST /documents`

Input:

* file upload
* optional `workspace_id`
* optional display title

Effect:

* stores raw file
* creates `UPLOADED`
* enqueues registration

Response:

* `doc_id`
* status
* upload metadata

### `GET /documents/{doc_id}/artifacts`

Returns:

* extraction summary
* normalization summary
* section summary
* chunk count
* current lifecycle state
* failure info if any

This is especially useful for validating the lifecycle before query features are added.

## 9. Recommended package layout

```text
src/doc_forge/
  app/
    api.py
    deps.py
    settings.py

  lifecycle/
    service.py
    orchestrator.py
    state_machine.py
    readiness.py

  stages/
    register.py
    extract.py
    normalize.py
    sectionize.py
    chunk.py
    index.py

  extractors/
    base.py
    markdown.py
    pdf.py

  normalizers/
    base.py
    markdown.py
    pdf.py

  indexing/
    base.py
    embeddings.py
    vector_store.py

  persistence/
    models.py
    documents.py
    sections.py
    chunks.py
    jobs.py
    events.py

  artifacts/
    schemas.py
    storage.py

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

The important separation is:

* **extractors** are format-specific
* **normalizers** map into one canonical representation
* **stages** mutate lifecycle state
* **persistence** owns storage concerns
* **domain** owns lifecycle-independent models

## 10. Readiness contract

A document becomes `READY` only if this predicate passes:

```python
def is_ready(doc_id: str) -> bool:
    return (
        document_exists(doc_id)
        and normalized_exists(doc_id)
        and section_count(doc_id) > 0
        and chunk_count(doc_id) > 0
        and index_count(doc_id) == chunk_count(doc_id)
        and all_chunks_have_doc_and_section(doc_id)
        and provenance_is_sufficient(doc_id)
        and not has_open_failure(doc_id)
    )
```

### Minimum provenance rule

For each chunk, require at least:

* `doc_id`
* `heading_path`
* one of:

  * `page range`
  * `source offsets`
  * `section identity`

This is a clean operationalization of the MVP traceability requirement.  

## 11. Validation plan

Your requirements already define the right validation shape. The test plan should mirror the lifecycle semantics rather than just asserting method calls. 

### Contract tests

* legal transitions only
* illegal transitions rejected
* `FAILED` reachable from each in-flight stage
* `READY` impossible without index + provenance

### Pipeline tests

* Markdown fixture reaches `READY`
* text PDF fixture reaches `READY`
* malformed PDF reaches `FAILED`
* unsupported file type rejected explicitly

### Persistence tests

* `Chunk -> Section -> Document` linkage intact
* no orphan sections
* no orphan chunks
* retry does not duplicate ownership

### Artifact tests

* normalized artifact preserves order
* heading paths non-empty
* PDF provenance includes page anchors when recoverable

## 12. Concrete decisions on your open questions

### Should normalization produce an explicit intermediate artifact?

**Yes.** Persist it.

Reason:

* better debugging
* stage-level retries
* easier validation
* makes `NORMALIZED` a real checkpoint

### How much PDF heading inference is necessary?

**Conservative inference only.**

Rule:

* infer when confidence is reasonable
* otherwise use coarse synthetic sections with page-based provenance
* never block `READY` just because deep hierarchy was not recoverable, but do block it if coarse provenance is missing

### Should indexing be synchronous or separate?

**Separate stage boundary; same worker execution is fine.**

That gives you:

* explicit retry semantics
* meaningful `INDEXED`
* no extra infrastructure burden for MVP

## 13. Local deployment model

For “local deployable service for now”, the cleanest deployment shape is:

```text
docker compose up
  - app/service container
  - sql database container
  - mounted local data volume
```

Or, if you want an even thinner first cut for engineering-only use:

```text
python -m doc_forge.app.api
python -m doc_forge.lifecycle.worker
```

with:

* local SQL database
* local data directory
* environment-configured index backend

The architectural point is not the packaging form. The point is that the lifecycle and artifacts remain identical in both modes.

## 14. What I would lock now

I would lock these decisions immediately:

1. **Single-node local service**
2. **DB-backed job queue**
3. **Explicit persisted normalized artifact**
4. **Section-first chunking**
5. **Separate `INDEXED` and `READY` checks**
6. **Conservative PDF structure inference**
7. **Filesystem artifacts + SQL metadata**
8. **Internal admin API only for MVP**

That combination is enough to deliver WS-004 without broadening product scope or smuggling in cloud complexity. It also preserves a clean path to later query lifecycle work.  

If useful, the next pass should turn this into a repo-facing ADR/architecture markdown with sequence diagrams and class/interface skeletons.
