# MVP: Question-Answering Service over PDF Books and Markdown Files


## 1. Problem

Engineers often have collections of technical books, manuals, notes, and internal documents in **PDF** and **Markdown** formats, but these materials are difficult to query as a single knowledge source.

The information exists, but it is trapped inside long-form documents that are slow to browse manually. Relevant content may be spread across multiple files, chapters, or sections. PDF books are particularly difficult because their structure is not always explicit, and Markdown files vary in organization and quality.

The consequence is repeated search loops, reading overhead, and decision risk when users cannot quickly verify what the corpus actually says.

As a result, users must manually search, skim, and cross-reference documents to answer even straightforward questions. Basic file search or keyword search is often not enough because it does not reliably provide:

- grounded answers based on the uploaded corpus
- references back to the relevant source material
- synthesis across multiple files
- a consistent way to work across PDF and Markdown inputs

The problem this MVP addresses is how to turn a collection of PDF books and Markdown files into a queryable knowledge base that can answer user questions and point back to the relevant source content.

## 2. Goal

Build a service where a user can:

- upload a focused collection of **PDF books** and **Markdown files**
- have those documents ingested into a unified internal corpus
- ask natural-language questions over the whole collection
- receive answers grounded in the uploaded documents
- inspect which documents, pages, chapters, or sections informed the answer

The MVP should prove that a focused mixed-format document collection can be converted into a usable **question-answering and evidence-inspection system** with source-backed responses.

## 3. Why This MVP Exists Now

This MVP validates whether engineers can get trustworthy answers from a bounded mixed-format corpus of PDFs and Markdown files, with inspectable evidence.

## 4. Product Definition

The MVP is a **document question-answering and evidence-inspection service** over a bounded user-provided corpus.

At a high level, the service performs four functions:

1. **Ingest** user-uploaded PDF and Markdown documents.
2. **Normalize and structure** the documents into an internal representation that preserves source boundaries and recoverable structure.
3. **Retrieve** relevant content for a user question from across the uploaded collection.
4. **Answer** the question using retrieved content and provide source references for inspection.

The product is successful if a user can reach a supported answer, inspect the evidence behind it, and recognize when the corpus does not support a confident response.

## 5. Users and Primary Jobs To Be Done

### Initial beta users

- engineers working with technical books, manuals, specs, and notes

### Possible expansion users after MVP

- researchers or students working with a focused reading corpus
- internal knowledge workers querying a personal or team document collection

### Primary jobs to be done

Users want to:

- find answers without manually reading entire books or notes
- ask focused questions in natural language over a bounded collection
- synthesize an answer from one or more relevant documents
- inspect the supporting evidence behind an answer
- navigate back to the source material behind an answer
- understand when the corpus does not support a reliable answer

## 6. Inputs

### Supported inputs in MVP

- **Text-based PDF files**
- **Markdown files**

### Input assumptions

- PDFs are primarily text-based and do not require OCR.
- PDF normalization is intentionally lightweight and aimed at recoverable text structure for retrieval and provenance, not exact layout reproduction.
- Markdown files are UTF-8 text and may contain headings, lists, paragraphs, and code blocks.
- Some Markdown files may originate from PDF-to-Markdown conversion.
- The service may accept a collection rather than a single file.

Internal architecture or workflow documents may use generic terms such as `document`, but MVP-supported inputs remain limited to text-based PDFs and Markdown files.

### Input metadata requirements

For each document, the system should preserve or derive, where possible:

- document identifier
- file name / display title
- source type (`pdf` or `markdown`)
- source reference within the service
- upload timestamp

## 7. In Scope

The MVP includes the following capabilities.

### 7.1 Document ingestion

- accept user-uploaded PDF and Markdown files
- register them as part of a single corpus for a user or workspace
- persist enough metadata to identify and retrieve those documents later

### 7.2 Structure recovery and normalization

- extract text from supported inputs
- recover document structure where possible
- construct section and header hierarchy from Markdown and from PDF-derived text when recoverable
- preserve document boundaries and coarse, recoverable source locations

For MVP, the system should emphasize **sections and headers** as the primary structural abstraction.
For PDFs, provenance should be recoverable at a coarse level such as page and inferred heading or section path when available; exact paragraph-level anchoring is not required.
Preserving code blocks or table-like fragments during normalization does not mean table-centric question answering or rich table understanding is in scope for MVP.

### 7.3 Retrieval preparation

- split documents into retrieval-ready units
- associate each unit with document and section context
- store enough metadata to trace a retrieval unit back to its source document and section path

### 7.4 Question answering over the corpus

- accept natural-language questions over the uploaded collection
- retrieve relevant content from one or more documents
- generate answers based on retrieved source material
- return source references with the answer

### 7.5 Source-grounded navigation

- show which documents contributed to an answer
- identify relevant sections, chapters, and pages when available
- allow a user to inspect the source backing the answer

## 8. Out of Scope

The following are explicitly deferred from MVP.

### 8.1 Input and parsing exclusions

- scanned PDFs that require OCR
- rich layout reconstruction
- special parsing for tables, diagrams, charts, and pictures
- figure understanding
- complex footnotes, sidebars, or margin annotations

### 8.2 Retrieval and indexing exclusions

- lexical index as a first-class retrieval layer
- advanced hybrid retrieval tuning
- sophisticated reranking pipelines beyond basic MVP needs

### 8.3 Derived knowledge exclusions

- stored summaries as a first-class artifact
- synthetic questions
- graph or entity-relation extraction
- precomputed derived knowledge views beyond core retrieval units

### 8.4 Product/platform exclusions

- collaboration and sharing
- multi-tenant permissions and ACL enforcement beyond simple ownership boundaries
- incremental sync from external drives or connectors
- workflow automation
- billing, quotas, or advanced admin controls
- production-grade observability and operations hardening

### 8.5 Question classes outside MVP

- questions requiring external world knowledge not present in the uploaded corpus
- questions whose answer depends mainly on tables, figures, or images
- exact scholarly citation formatting
- strong compare-and-contrast behavior that depends on deliberate source diversification or exhaustive coverage of differing views
- guaranteed exhaustive retrieval over very large corpora

## 9. Primary Use Cases

### 9.1 Factual lookup

Examples:

- “What is X?”
- “How does this book define Y?”
- “What are the requirements for Z?”

### 9.2 Localized explanation

Examples:

- “Explain the retry strategy described in these notes.”
- “Summarize the chapter’s explanation of backpropagation.”

### 9.3 Multi-source synthesis

Examples:

- “What do these documents say about vector databases?”
- “Synthesize the guidance on caching from Book A and my notes.”

The MVP may synthesize across multiple relevant documents and show the supporting sources, but this is secondary to the core promise of grounded answers and inspectable evidence. It does not promise strong compare-and-contrast behavior across all relevant viewpoints.
When sources differ or support is incomplete, the system may surface uncertainty, narrow the scope of the answer, or abstain rather than imply exhaustive reconciliation.

### 9.4 Source navigation

Examples:

- “Where is tokenization discussed?”
- “Which book or section covers distributed transactions?”
- “Show the passages relevant to this question.”

## 10. Success Criteria

The MVP is successful if a user can:

- upload a small collection of PDF and Markdown documents
- ask a question over that collection
- receive an answer based primarily on retrieved source content
- inspect which source documents and sections informed the answer
- understand when the corpus does not contain enough evidence for a reliable answer
- decide whether to trust the answer by inspecting the supporting evidence

From an engineering perspective, success means:

- the service ingests both supported file types into one corpus
- structure recovery is good enough to identify documents and sections reliably in common cases
- retrieval works across document boundaries
- generated answers remain tied to source references
- failure cases are transparent rather than fabricated

## 11. Non-Goals

This MVP is **not** intended to:

- fully understand arbitrary PDFs
- solve OCR and layout reconstruction
- replace deep manual reading for all workflows
- provide perfect answers for every question type
- support every document format from day one
- act as a general-purpose research agent over the public web

## 12. Invariants and Hard Requirements

These are the properties that should remain true even if implementation details change. Together they define the MVP trust contract.

### 12.1 Stable document identity

Each uploaded document must have a stable internal identifier so the system can track it throughout ingestion, retrieval, and answer generation.

### 12.2 Structural integrity

Recovered section and header relationships must form a valid document hierarchy where such structure is present or can be inferred.

### 12.3 Traceability

Each retrieval unit used for answering must be traceable back to:

- its source document
- its section or chapter path when available
- its page or source location when available

For PDFs, this traceability may be coarse. The system must preserve recoverable provenance, but it does not need to guarantee exact paragraph-level anchors in MVP.

### 12.4 Grounded answering

Answers must be based on retrieved corpus content rather than unsupported model inference. The system must not fabricate supporting provenance for a claim.

### 12.5 Honest failure behavior

When the corpus does not contain enough evidence, the system should narrow scope, abstain, or say so explicitly rather than produce a confident unsupported answer.

## 13. Answer Quality Expectations

For MVP, answers should be:

- grounded in retrieved source content
- limited to what the uploaded corpus supports
- explicit about uncertainty when evidence is weak
- accompanied by source references useful for inspection
- willing to narrow scope or abstain when support is insufficient

The service should prefer a qualified answer such as:

> I could not find enough support in the uploaded documents.

rather than provide unsupported synthesis.

## 14. Proposed User Experience

A minimal end-to-end user flow is:

1. The user uploads one or more PDF and Markdown files.
2. The service ingests and structures the collection.
3. The user asks a question in natural language.
4. The service retrieves relevant content from the corpus.
5. The service returns:
   - an answer
   - the supporting sources
   - enough source detail to inspect the origin of the answer

The user should be able to treat the corpus as a single question-answerable workspace.

## 15. Implementation Boundary for MVP

This document defines the product promise and minimum trust guarantees for MVP. It intentionally does not lock the team into a detailed retrieval or representation design.

Framing authority: this document governs MVP product scope, supported inputs, trust guarantees, and explicit deferrals. `docs/evergreen/functional-requirements.md` owns the minimal functional requirements and acceptance criteria. `docs/evergreen/lifecycle-and-evidence-flow.md` owns conceptual lifecycle controls. Architecture and workflow documents may generalize internal concepts for modeling or implementation, but they may not broaden the MVP on their own.

For MVP, implementation choices should satisfy the 12 minimal functional requirements while preserving these trust boundaries:

- supported uploads remain limited to text-based PDFs and Markdown
- corpora remain bounded to the selected user or workspace scope
- source identity, source type, local text context, and recoverable provenance survive ingestion, retrieval, answering, and evidence rendering
- PDF normalization remains lightweight and focused on recoverable text and provenance, not OCR, rich layout reconstruction, figures, charts, images, or table-centric QA
- retrieval and answering use only active corpus evidence
- answers may synthesize across one or more relevant documents only when the retrieved evidence supports the material claims
- weak evidence, weak provenance, unsupported capability, or missing corpus support must produce narrowing, qualification, explicit limitation language, or abstention

The exact internal schema, retrieval-unit semantics, metadata payloads, anchor model, context-assembly policy, and evaluation strategy belong in architecture and workflow documents rather than this framing doc.

## 16. Deferred Work

The following items are intentionally deferred to later versions.

### 16.1 Parsing and structure

- OCR for scanned PDFs
- special handling for tables
- special handling for figures, diagrams, and pictures
- richer anchor systems and layout-aware citation

### 16.2 Retrieval

- lexical index
- hybrid retrieval tuning
- advanced reranking
- very large corpus optimization

### 16.3 Derived knowledge

- summaries
- synthetic questions
- graph extraction
- entity resolution and knowledge graph workflows

### 16.4 Product surface

- cloud-drive connectors
- sharing and team workspaces
- background synchronization
- administrative controls
- operational dashboards and full production hardening

## 17. Open Questions

These decisions are intentionally left open for the next design pass.

1. What maximum corpus size should MVP support reliably?
2. What minimum source reference should be exposed to users for PDFs: page only, page plus heading, or page plus inferred section path?
3. How should the product behave for malformed or weakly structured documents?
4. How much PDF structure recovery is required before the product is considered useful?
5. What answer UI is sufficient for source inspection in MVP?
