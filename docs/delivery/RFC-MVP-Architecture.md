# RFC: MVP Architecture and Engineering Topology for Document QA over PDF and Markdown

**Status:** Draft  
**Scope:** MVP / Version 1  
**Last updated:** 2026-03-08

---

## 1. Purpose

This document defines the engineering operating model and system architecture that should follow the MVP framing for the document question-answering service.

It translates the product framing into:

- a precise runtime model
- a domain-based engineering topology
- explicit cross-domain contracts
- a phased execution plan
- a standardized artifact structure for ongoing delivery

This document is intended to be an evergreen architectural note. It should describe the current intended system shape for MVP, not the temporary state of a particular implementation effort.

---

## 2. Context

The MVP is a service where a user can upload a collection of **text-based PDF books** and **Markdown files**, ask natural-language questions across that collection, receive answers grounded in the uploaded corpus, and inspect the source material that informed the answer.

The MVP is intentionally constrained. It is not attempting to solve arbitrary document understanding. It is attempting to prove that a mixed-format corpus can be normalized well enough to support useful retrieval and source-grounded generation with inspectable provenance.

This architecture must remain aligned with the MVP framing:

- supported inputs are text-based PDFs and Markdown files
- sections and headers are the primary structural abstraction
- answers must remain grounded in retrieved corpus content
- source traceability is mandatory
- honest failure behavior is mandatory
- OCR, lexical index as a first-class layer, advanced reranking, stored summaries, synthetic questions, graph extraction, table/figure specialization, and external-world knowledge are deferred beyond MVP

---

## 3. Core architectural position

The system should be designed as **one Core Request Lifecycle** and implemented through **multiple Functional Domains** with strict interface contracts.

This distinction is important.

The product experience must behave like one coherent pipeline:

1. the user uploads source files
2. the system ingests and normalizes them
3. the system prepares retrieval-ready units
4. the user asks a question
5. the system retrieves evidence and generates an answer
6. the user inspects the provenance behind the answer

That is the **System Critical Path**.

The engineering organization should **not** mirror that path as a serial handoff chain. For a small team, that would create bottlenecks, unclear ownership, and poor integration behavior.

The recommended operating model is therefore:

- **one runtime path**
- **multiple bounded engineering contexts**
- **shared contracts across those contexts**
- **continuous validation against the same end-to-end path**

---

## 4. Assumptions and constraints

### 4.1 Team scale

The expected team size is small, approximately **4-8 engineers**.

The topology therefore avoids over-fragmentation. Too many fine-grained subsystem boundaries would create integration overhead, local optimization, and Conway's Law pathologies.

### 4.2 Domain ownership model

Each domain owner should be capable of end-to-end execution inside that domain boundary. For example, a Search & Grounded Generation engineer may own vector retrieval logic, prompt construction, and the necessary API behavior within that bounded context.

### 4.3 MVP scope discipline

The architecture must remain strict about MVP boundaries. Time-to-value matters more than solving every long-term systems problem.

Specifically for MVP:

- no OCR for scanned PDFs
- no general-purpose layout reconstruction
- no first-class lexical retrieval layer
- no advanced hybrid tuning as a prerequisite
- no extensive figure/table understanding
- no external-world knowledge dependency
- no first-class precomputed summaries or synthetic questions
- no production-grade observability program as a gating dependency

### 4.4 Contract discipline

While domains are bounded, the contracts between them must be globally defined and stable enough to support concurrent implementation.

### 4.5 Source-groundedness is not optional

The system must optimize for groundedness and inspectability, not only answer fluency. A more cautious answer with reliable provenance is preferable to a broader answer with weak evidence.

---

## 5. Terminology

The following terminology should be used consistently in architecture and planning documents.

| Legacy / lower-level phrasing | Preferred terminology | Meaning |
| --- | --- | --- |
| backbone flow | **System Critical Path** / **Core Request Lifecycle** | The runtime execution path of the product |
| workstreams / lanes | **Functional Domains** / **Bounded Contexts** | Engineering ownership boundaries |
| corpus and ingestion | **Data Platform & Ingestion** | Source-of-truth intake and persistence layer |
| structure recovery | **Parsing & Structural Normalization** | Transform heterogeneous source formats into a common schema |
| segmentation / chunking | **Semantic Discretization** | Turn normalized documents into searchable retrieval units |
| retrieval | **Vector Search & Context Assembly** | Retrieve and prepare evidence for generation |
| answering + citation contract | **Grounded Generation (RAG) Subsystem** | Synthesize bounded answers with evidence mapping |
| source inspection UI | **Provenance Verification Surface** | User-facing surface for validating answer origin |
| evaluation and quality gates | **LLMOps & Evaluation Framework** | Offline and online quality measurement and gating |

Two notes:

1. **Semantic Discretization** is precise, but in code and implementation docs, `retrieval units` or `segments` may still be the clearer operational term.
2. **Grounded Generation** should be treated as an architectural subsystem, not merely an LLM call.

---

## 6. System Critical Path

The MVP runtime path should be defined as follows.

### 6.1 File intake

The user uploads one or more source files.

Supported file types in MVP:

- text-based PDF
- Markdown

The system registers each file into a corpus with stable identity and basic metadata.

### 6.2 Parsing and structural normalization

The system converts the raw source into a normalized internal representation that preserves:

- document boundaries
- recoverable section and heading hierarchy
- source location metadata
- source type and file identity

Markdown should contribute explicit heading structure directly. PDF should contribute page-aware text plus inferred hierarchy where possible.

### 6.3 Semantic discretization

The normalized document is split into retrieval-ready units tied to structural context.

Each retrieval unit must remain traceable to:

- a source document
- a section or heading path when available
- a page or source location when available

### 6.4 Retrieval

When the user asks a question, the system retrieves relevant units from one or more documents in the corpus.

Retrieval must work across document boundaries and preserve enough metadata for later provenance display.

### 6.5 Context assembly

The system assembles retrieved evidence into a bounded context for generation.

This includes:

- ordering
- deduplication
- optional neighbor expansion
- respecting context budget
- preserving evidence anchors

### 6.6 Grounded generation

The answering layer generates a response constrained by retrieved evidence.

It should:

- stay bounded by retrieved content
- prefer qualified uncertainty over unsupported inference
- include evidence references in a user-inspectable form

### 6.7 Provenance verification

The user receives both:

- the answer
- the supporting evidence references

The user must be able to inspect the origin of the answer through document, section, and page-level references where available.

---

## 7. Functional domain topology

The recommended topology is four Functional Domains.

### 7.1 Domain 1: Data Platform & Ingestion

**Scope:** system of record for corpus intake and persistence.

**Owns:**

- upload APIs and file registration
- document identity generation
- source metadata persistence
- corpus membership and indexing metadata
- storage of raw source artifacts and normalized lineage references
- document lifecycle state within MVP

**Responsibilities:**

- accept source files into the service
- assign stable `doc_id`
- preserve filename, display title, source type, upload timestamp, and internal storage reference
- maintain authoritative corpus membership
- expose retrieval-independent metadata services to downstream domains

**Primary contract:** canonical `Document` model

Example minimal shape:

```json
{
  "doc_id": "string",
  "title": "string",
  "filename": "string",
  "source_type": "pdf|markdown",
  "storage_ref": "string",
  "uploaded_at": "timestamp",
  "metadata": {}
}
```

**Non-goals in MVP:**

- multi-tenant policy sophistication
- connectors and sync engines
- advanced ACL propagation
- ingestion automation beyond explicit upload

**Key failure modes:**

- unstable document identity
- mismatched source metadata
- raw/normalized lineage breaks
- duplicate corpus registration behavior

---

### 7.2 Domain 2: Parsing & Structural Normalization

**Scope:** convert heterogeneous inputs into a common structural representation.

**Owns:**

- Markdown parsing
- PDF text extraction
- page boundary preservation
- heading and section recovery heuristics
- normalized structure schema
- location metadata sufficient for provenance resolution

**Responsibilities:**

- parse Markdown using heading hierarchy directly
- extract text from text-based PDFs
- infer recoverable document structure from PDF text/layout patterns or PDF-derived Markdown representations
- output a structurally coherent representation consumable by downstream discretization and retrieval systems

**Primary contract:** normalized document payload with structure and location metadata

Example minimal shape:

```json
{
  "doc_id": "string",
  "title": "string",
  "source_type": "pdf|markdown",
  "pages": [
    { "page_number": 1, "text": "..." }
  ],
  "sections": [
    {
      "section_id": "string",
      "parent_id": "string|null",
      "heading": "string",
      "path": ["Chapter 1", "Intro"],
      "page_span": [1, 3],
      "text": "..."
    }
  ],
  "metadata": {}
}
```

**Non-goals in MVP:**

- OCR
- perfect layout fidelity
- general visual understanding of figures or images
- full scholarly PDF reconstruction
- first-class table-as-data extraction

**Key failure modes:**

- missing or malformed hierarchy
- page mapping loss
- over-aggressive heading inference
- structurally valid but semantically poor normalization

**Architectural note:**

This domain should optimize for **segmentable, traceable text**, not for visual reproduction.

---

### 7.3 Domain 3: Search & Grounded Generation

**Scope:** core RAG intelligence layer.

**Owns:**

- semantic discretization policy
- embedding generation
- vector indexing
- retrieval logic
- context assembly rules
- prompt construction
- answer generation bounded by evidence
- evidence-to-answer mapping

This domain intentionally combines what is often split into separate “retrieval” and “generation” teams. For MVP, keeping them together reduces cross-team friction on the most coupled intelligence path.

**Responsibilities:**

- turn normalized documents into retrieval units
- preserve section-aware and source-aware metadata on every retrieval unit
- index units for semantic search
- retrieve evidence for user questions
- assemble evidence into coherent context under token budget
- generate responses constrained to available evidence
- emit citations or evidence references in the defined answer schema

**Primary contracts:**

1. `RetrievalUnit` schema
2. `Answer` payload schema

Example minimal `RetrievalUnit`:

```json
{
  "unit_id": "string",
  "doc_id": "string",
  "section_id": "string|null",
  "section_path": ["Chapter 1", "Intro"],
  "page_span": [1, 1],
  "text": "string",
  "anchor": "string",
  "metadata": {}
}
```

Example minimal `Answer` payload:

```json
{
  "answer_text": "string",
  "evidence": [
    {
      "doc_id": "string",
      "title": "string",
      "anchor": "string",
      "section_path": ["..."],
      "page_span": [1, 1],
      "snippet": "string"
    }
  ],
  "abstained": false,
  "reason": null
}
```

**Non-goals in MVP:**

- first-class lexical index as a required layer
- advanced hybrid retrieval tuning
- sophisticated reranking pipelines as a gating dependency
- autonomous multi-hop agent behavior over the corpus
- external knowledge augmentation

**Key failure modes:**

- topical dilution from poor discretization
- retrieval misses across documents
- incoherent context assembly
- unsupported answer synthesis
- citations that do not actually support claims

**Architectural note:**

The generation subsystem must be optimized for **faithfulness and provenance**, not just helpfulness.

---

### 7.4 Domain 4: Product Surface & LLMOps

**Scope:** user trust surface and quality system.

**Owns:**

- user-facing application behavior for asking questions and viewing answers
- provenance verification surface
- evaluation dataset design and maintenance
- offline evaluation pipeline
- unsupported-claim checks and quality gates
- release criteria tied to user-verifiable outcomes

**Responsibilities:**

- render answer payloads in a way that supports source inspection
- expose document/section/page references in a minimally usable interface
- define evaluation suites for factual lookup, localized explanation, multi-source synthesis, and source navigation
- measure groundedness, citation precision, abstention behavior, and retrieval adequacy
- create quality gates for MVP progression and release

**Primary contract:** provenance inspection model and evaluation outputs

Example minimal provenance view model:

```json
{
  "answer_text": "string",
  "sources": [
    {
      "title": "string",
      "section_label": "string|null",
      "page_label": "p. 12",
      "snippet": "string",
      "anchor": "string"
    }
  ]
}
```

**Non-goals in MVP:**

- fully mature analytics platform
- advanced online experimentation framework
- collaboration workflow surfaces
- production-grade operational dashboards as a dependency for initial value validation

**Key failure modes:**

- provenance exists in data but is unusable in UI
- evaluation only measures answer fluency and ignores groundedness
- offline quality gates diverge from actual user trust conditions

---

## 8. Cross-domain contracts

The first execution step after MVP framing should be to freeze a minimal set of interface contracts.

These contracts are the anti-chaos mechanism for concurrent engineering.

### 8.1 Required shared contracts

At minimum, define and version the following:

1. `Document`
2. `NormalizedDocument`
3. `Section`
4. `RetrievalUnit`
5. `Answer`
6. `EvidenceReference`
7. `ProvenanceViewModel`

### 8.2 Contract requirements

All contracts should make the following explicit:

- stable identifiers
- required vs optional fields
- source type handling
- nullability rules
- location semantics
- versioning expectations
- failure and partial-output semantics

### 8.3 Invariants across all contracts

The following invariants should hold throughout MVP:

- every uploaded document has a stable internal identifier
- every retrieval unit can be traced to a document and source location
- every answer evidence reference can be resolved back to a document location exposed to the user
- the system may return partial structure, but must not fabricate provenance
- abstention is valid when evidence is insufficient

---

## 9. Data model baseline

The MVP should keep the internal model minimal.

### 9.1 Document

Represents a user-uploaded source artifact.

Required properties:

- `doc_id`
- `title` or display title
- `filename`
- `source_type`
- `upload timestamp`
- storage reference

### 9.2 Section

Represents a recoverable structural unit, usually heading-scoped.

Required properties:

- `section_id`
- `doc_id`
- `parent_id` or root reference
- `heading`
- `section_path`
- optional `page_span`

### 9.3 RetrievalUnit

Represents the retrieval-ready unit used for vector indexing and answer grounding.

Required properties:

- `unit_id`
- `doc_id`
- `section_id` when available
- `section_path` when available
- `text`
- `anchor`
- optional `page_span`

### 9.4 EvidenceReference

Represents a cited or inspectable answer support item.

Required properties:

- `doc_id`
- display title
- anchor
- snippet
- location label or machine-readable location

### 9.5 Answer

Represents the answer payload returned to the product surface.

Required properties:

- answer text
- list of evidence references
- abstention or insufficiency signal
- optional explanation for insufficient evidence

---

## 10. Semantic discretization policy

The architecture should treat segmentation as a first-class quality lever, even in MVP.

### 10.1 Why it matters

Poor segmentation causes:

- retrieval precision loss from mixed-topic passages
- broken evidence boundaries
- worse citation quality
- unnecessary context waste
- higher unsupported-claim risk during generation

### 10.2 MVP policy direction

For MVP, discretization should:

- respect section boundaries where possible
- preserve code blocks as atomic units when practical
- avoid splitting mid-thought where possible
- produce retrieval units large enough for semantic coherence but small enough for precise retrieval
- maintain deterministic or near-deterministic structure for debugging and evaluation

### 10.3 Practical expectation

The exact heuristic may evolve, but the resulting retrieval units must remain:

- traceable
- structurally anchored
- suitable for evidence display
- stable enough for evaluation reproducibility

---

## 11. Retrieval and context assembly policy

The retrieval layer should be architected as **Vector Search & Context Assembly**, not merely nearest-neighbor lookup.

### 11.1 Retrieval expectations

MVP retrieval should:

- work across multiple documents
- preserve document and section metadata
- support source-grounded answering rather than free-form semantic similarity only

### 11.2 Context assembly expectations

The context assembler should:

- order evidence deterministically
- avoid excessive duplication
- optionally include minimal neighboring context when necessary for coherence
- remain within a defined token budget
- preserve anchors needed for later provenance rendering

### 11.3 MVP exclusions

Do not make these prerequisites for initial delivery:

- sophisticated reranking stack
- lexical-vector fusion as a required foundation
- large-scale corpus optimization
- extensive query planning logic

---

## 12. Grounded generation policy

The answering layer must behave as a **Grounded Generation subsystem** rather than an unconstrained summarizer.

### 12.1 Primary behaviors

The subsystem should:

- consume retrieved evidence
- generate a bounded response
- cite or reference the supporting evidence
- avoid asserting unsupported claims
- abstain or qualify when evidence is weak or absent

### 12.2 Preferred failure behavior

When evidence is insufficient, the system should return a qualified failure such as:

> I could not find enough support in the uploaded documents.

That is preferable to plausible but unsupported synthesis.

### 12.3 Quality definition

Answer quality in MVP is defined by:

- groundedness
- provenance clarity
- relevance to the question
- appropriate uncertainty behavior

Not by maximal completeness or rhetorical polish.

---

## 13. Provenance verification surface

A source-grounded system without a usable provenance surface is incomplete.

### 13.1 MVP requirements

The product surface must let the user inspect:

- which documents informed the answer
- which sections or headings were relevant when available
- which pages were relevant for PDFs when available
- a snippet or excerpt sufficient to understand why the evidence was used

### 13.2 Minimum viable provenance UI

The MVP interface can remain simple, but it should expose:

- answer text
- evidence list
- document title
- section label or inferred path when available
- page label for PDFs when available
- snippet preview

### 13.3 Anti-pattern

Do not treat citations as decorative footnotes. In this product, provenance is a primary trust mechanism.

---

## 14. LLMOps and evaluation framework

The system should ship with an MVP-appropriate evaluation framework.

### 14.1 Evaluation categories

The evaluation suite should cover at least four use-case classes:

1. factual lookup
2. localized explanation
3. multi-source synthesis
4. source navigation

### 14.2 Offline evaluation dimensions

Measure at least:

- retrieval adequacy
- answer correctness where practical
- unsupported-claim rate
- citation precision
- abstention behavior when evidence is absent

### 14.3 Golden corpus

Maintain a small representative corpus that includes:

- Markdown files with headings
- text-based PDFs with recoverable hierarchy
- weakly structured documents
- code-heavy or technical prose documents where relevant

### 14.4 Release gates

MVP should not be considered ready unless:

- both file types ingest into one corpus
- structure recovery is usable in common cases
- retrieval works across documents
- answer evidence is inspectable
- failure behavior is honest

---

## 15. Execution phasing

The work should proceed in four phases.

### Phase 1: Interface-First Design

**Action:** define and freeze minimal schemas and contracts.

Deliverables:

- corpus model
- normalized structure model
- retrieval unit schema
- answer payload schema
- evidence reference model

**Why:** this unblocks concurrent domain execution while minimizing integration churn.

---

### Phase 2: Walking Skeleton

**Action:** build the thinnest real end-to-end path through the System Critical Path.

Recommended initial slice:

- upload a small corpus of PDFs and Markdown files
- normalize them
- create retrieval units
- index them semantically
- answer a question
- return evidence references

**Why:** this proves that the architecture is viable before deep local optimization.

---

### Phase 3: Domain-Specific Hardening

**Action:** improve each domain locally while preserving contracts.

Examples:

- better PDF section inference
- better discretization heuristics
- improved context assembly
- more robust provenance rendering
- stronger evaluation coverage

**Why:** once the walking skeleton exists, local iteration becomes much safer and more measurable.

---

### Phase 4: End-to-End Validation and Release Gating

**Action:** run the evaluation framework against the integrated system and validate release criteria.

Check:

- groundedness
- citation correctness
- retrieval sufficiency on representative questions
- abstention quality when evidence is absent
- usability of the provenance verification surface

**Why:** MVP should be released on trust and utility criteria, not on subsystem completeness.

---

## 16. Team topology recommendation

For a team of 4-8 engineers, the recommended mapping is:

### Team A — Data Platform & Ingestion

Focus:

- upload path
- source-of-truth corpus model
- persistence and file lifecycle

### Team B — Parsing & Structural Normalization

Focus:

- Markdown parser
- PDF extraction
- hierarchy recovery
- normalized output fidelity

### Team C — Search & Grounded Generation

Focus:

- retrieval units
- embeddings and vector index
- context assembly
- answer generation and evidence mapping

### Team D — Product Surface & LLMOps

Focus:

- answer inspection UX
- evaluation dataset and pipeline
- quality gates
- trust-oriented release readiness

This topology is specific enough for ownership while still compact enough to avoid excessive coordination cost.

---

## 17. Standardized artifact topology

The documentation tree should separate stable architecture from temporal execution.

### 17.1 Evergreen architecture

Recommended top-level evergreen artifact:

- `RFC-MVP-Architecture.md`

Purpose:

- define system boundaries
- define functional domains
- define shared contracts
- define the System Critical Path
- define release-quality expectations

### 17.2 Domain specifications

Recommended evergreen domain documents:

- `Domain-Data-Platform.md`
- `Domain-Structural-Normalization.md`
- `Domain-Search-And-Generation.md`
- `Domain-Provenance-And-Eval.md`

Each should describe:

- scope
- owned responsibilities
- interfaces in and out
- invariants
- non-goals
- primary failure modes
- validation expectations

### 17.3 Temporal work artifacts

Active implementation should live under workstreams rather than being embedded into architecture notes.

Recommended structure per workstream:

- `workstream.md`
- `status.md`
- `adr-log.md`
- `telemetry-and-evals.md`
- `handoff.md` when needed

This keeps evergreen truth separate from work history and preserves resumability.

---

## 18. Immediate next artifacts after this RFC

After this architecture note, the next highest-value artifacts are:

1. **Domain specifications** for each Functional Domain
2. **Schema definitions** for shared contracts
3. **Walking skeleton implementation plan** tied to the System Critical Path
4. **Evaluation plan** for MVP release gating

Recommended file set:

- `Domain-Data-Platform.md`
- `Domain-Structural-Normalization.md`
- `Domain-Search-And-Generation.md`
- `Domain-Provenance-And-Eval.md`
- `Schemas-Corpus-And-Answer-Payloads.md`
- `Plan-Walking-Skeleton.md`
- `Plan-MVP-Evaluation.md`

---

## 19. Open design decisions for the next pass

This RFC intentionally does not fully resolve the following questions:

1. What maximum corpus size should MVP support reliably?
2. What minimum PDF provenance should be exposed to users: page only, page plus heading, or page plus inferred section path?
3. How should malformed or weakly structured documents be represented when normalization is partial?
4. What discretization policy should be used for very short or very long sections?
5. How much PDF hierarchy recovery is necessary before the product is considered useful?
6. What exact answer-and-provenance UI is sufficient for MVP?
7. How deterministic should the normalization and discretization pipeline be in practice for debugging and evaluation?

These are the correct next technical design questions. They should be resolved without expanding scope into deferred features.

---

## 20. Final position

The architectural position for MVP is:

**One Core Request Lifecycle, implemented by four Functional Domains, with strict shared contracts and release decisions driven by groundedness and provenance quality.**

The product should feel like one coherent document intelligence pipeline.

The engineering organization should behave as concurrent bounded contexts aligned to that pipeline, not as a linear chain of serial handoffs.

That is the simplest topology that supports:

- fast MVP delivery
- clean ownership
- bounded complexity
- strong source traceability
- trustworthy user outcomes

