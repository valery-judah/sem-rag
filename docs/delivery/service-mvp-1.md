# MVP: Question-Answering Service over PDF Books and Markdown Files

**Status:** Draft  
**Scope:** MVP / Version 1  
**Last updated:** 2026-03-08

## 1. Problem

Users often have collections of technical books, manuals, notes, and internal documents in **PDF** and **Markdown** formats, but these materials are difficult to query as a single knowledge source.

The information exists, but it is trapped inside long-form documents that are slow to browse manually. Relevant content may be spread across multiple files, chapters, or sections. PDF books are particularly difficult because their structure is not always explicit, and Markdown files vary in organization and quality.

As a result, users must manually search, skim, and cross-reference documents to answer even straightforward questions. Basic file search or keyword search is often not enough because it does not reliably provide:

- grounded answers based on the uploaded corpus
- references back to the relevant source material
- synthesis across multiple files
- a consistent way to work across PDF and Markdown inputs

The problem this MVP addresses is how to turn a collection of PDF books and Markdown files into a queryable knowledge base that can answer user questions and point back to the relevant source content.

## 2. Goal

Build a service where a user can:

- upload a collection of **PDF books** and **Markdown files**
- have those documents ingested into a unified internal corpus
- ask natural-language questions over the whole collection
- receive answers grounded in the uploaded documents
- inspect which documents, pages, chapters, or sections informed the answer

The MVP should prove that a mixed-format document collection can be converted into a usable **question-answering system** with source-backed responses.

## 3. Why This MVP Exists Now

This MVP exists to validate three core assumptions:

1. Users derive real value from asking questions over their own document collections rather than searching files manually.
2. PDF and Markdown sources can be normalized well enough to support useful retrieval and source-grounded answers.
3. A single service can provide better utility than isolated file browsing or keyword search by combining ingestion, retrieval, and grounded answer generation.

The objective is not to solve every document-processing problem. The objective is to validate that this product shape is useful and technically viable with a constrained first version.

## 4. Product Definition

The MVP is a **document question-answering service** over a user-provided corpus.

At a high level, the service performs four functions:

1. **Ingest** user-uploaded PDF and Markdown documents.
2. **Normalize and structure** the documents into an internal representation that preserves source boundaries and recoverable structure.
3. **Retrieve** relevant content for a user question from across the uploaded collection.
4. **Answer** the question using retrieved content and provide source references for inspection.

The product is successful if a user can treat the uploaded corpus as a single searchable and answerable knowledge base.

## 5. Users and Primary Jobs To Be Done

### Primary users

- engineers working with technical books, manuals, specs, and notes
- researchers or students working with a focused reading corpus
- internal knowledge workers querying a personal or team document collection

### Primary jobs to be done

Users want to:

- find answers without manually reading entire books or notes
- ask focused questions in natural language
- compare what different sources say about the same topic
- locate the source material behind an answer
- use one interface over many documents instead of opening files one by one

## 6. Inputs

### Supported inputs in MVP

- **Text-based PDF files**
- **Markdown files**

### Input assumptions

- PDFs are primarily text-based and do not require OCR.
- Markdown files are UTF-8 text and may contain headings, lists, paragraphs, and code blocks.
- Some Markdown files may originate from PDF-to-Markdown conversion.
- The service may accept a collection rather than a single file.

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
- preserve document boundaries and coarse source locations

For MVP, the system should emphasize **sections and headers** as the primary structural abstraction.

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
- “Compare how Book A and my notes describe caching.”

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

These are the properties that should remain true even if implementation details change.

### 12.1 Stable document identity

Each uploaded document must have a stable internal identifier so the system can track it throughout ingestion, retrieval, and answer generation.

### 12.2 Structural integrity

Recovered section and header relationships must form a valid document hierarchy where such structure is present or can be inferred.

### 12.3 Traceability

Each retrieval unit used for answering must be traceable back to:

- its source document
- its section or chapter path when available
- its page or source location when available

### 12.4 Grounded answering

Answers must be based on retrieved corpus content rather than unsupported model inference.

### 12.5 Honest failure behavior

When the corpus does not contain enough evidence, the system should say so rather than produce a confident unsupported answer.

## 13. Answer Quality Expectations

For MVP, answers should be:

- grounded in retrieved source content
- limited to what the uploaded corpus supports
- explicit about uncertainty when evidence is weak
- accompanied by source references useful for inspection

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

## 15. Technical Direction for MVP

This section describes implementation direction at a high level without locking the team into a detailed build spec.

### 15.1 Corpus model

The system should maintain a corpus composed of documents, sections, and retrieval units.

A reasonable minimal internal model is:

- **Document**
  - `doc_id`
  - title / filename
  - source type
  - metadata
- **Section**
  - section identifier
  - parent section or document
  - section path / heading path
  - optional page span
- **Retrieval unit**
  - chunk identifier
  - parent section
  - text content
  - source references

### 15.2 Parsing direction

For Markdown:

- parse headings and section boundaries directly
- preserve heading order and hierarchy
- treat paragraphs and code blocks as content blocks

For PDFs:

- extract text from text-based PDFs
- recover page boundaries
- infer section and header structure where possible from layout/text patterns or PDF-derived Markdown representations

### 15.3 Retrieval direction

The service should support retrieval over the document corpus using chunked content tied to document and section metadata.

The MVP does not require a lexical index. The retrieval layer may initially rely on a semantic representation plus metadata linking back to source context.

### 15.4 Answer generation direction

The answering layer should:

- consume retrieved content
- synthesize a response bounded by that content
- return source references in a form the user can inspect

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
3. How should the system represent malformed or weakly structured documents?
4. What chunking policy should be used for very short or very long sections?
5. How much PDF structure recovery is required before the product is considered useful?
6. What answer UI is sufficient for source inspection in MVP?

## 18. Summary

This MVP is a focused service for asking questions over a user-uploaded collection of PDF books and Markdown files.

It is intentionally constrained.

Version 1 is about proving that the system can:

- ingest a mixed-format corpus
- recover enough structure to support retrieval
- answer questions over the uploaded documents
- ground those answers in identifiable source material

It is not yet about full document intelligence, advanced parsing, or extensive derived knowledge generation.
