# Retrieval Unit Design — Current-System Result

> Historical note: this workstream note is retained as temporary analysis only. Canonical ownership of the retrieval hierarchy, shared structural concepts, and concept-to-implementation mapping has moved to [`docs/evergreen/retrieval-hierarchy.md`](../../evergreen/retrieval-hierarchy.md).

## Purpose

This note records the current implementation truth for section 8 of the walkthrough outline:

- what the retrieval unit is today,
- what metadata it carries,
- how strongly it preserves section semantics,
- and where it differs from the desired first-slice framing.

This is a current-system result, not a target redesign.

## Short answer

The current retrieval unit is a `chunk`, not a whole section.

More precisely, the system uses **section-aware passage chunks**:

- sections are recovered first,
- chunks are derived inside those sections,
- dense retrieval ranks chunks,
- later selection and citation logic preserve the chunk's document and section anchors.

So the implementation is already provenance-aware and section-linked, but it is still **passage-first**, not **section-first**.

## Current design in the code

### 1. Sections are recovered before chunking

Markdown structure is recovered into `Section` records with:

- `section_id`
- `doc_id`
- `heading_path`
- `depth`
- `parent_section_id`
- optional page and source offsets

The Markdown section derivation logic builds a nested heading stack and assigns stable section ids like `{doc_id}:section:{ordinal}`.

Relevant code:

- `src/doc_forge/structure/sections.py`
- `src/doc_forge/corpus/models.py`

### 2. Chunking is section-aware

Chunking groups normalized content blocks by recovered section and emits `Chunk` records with:

- `chunk_id`
- `doc_id`
- `section_id`
- `text`
- `ordinal`
- `heading_path`
- optional page span
- optional source offsets

This means chunks are not arbitrary global windows across the document. They are anchored to one recovered section.

Relevant code:

- `src/doc_forge/chunking/service.py`
- `src/doc_forge/chunking/policy.py`
- `src/doc_forge/corpus/models.py`

### 3. Splitting rules are passage-oriented

The current chunker keeps blocks together until one of these conditions forces a split:

- the coarse token count would exceed `MAX_TOKENS_PER_CHUNK = 120`
- the block is a code block, which is flushed as its own boundary

So the retrieval unit is usually:

- one whole small section, or
- one bounded passage inside a larger section

It is not necessarily identical to the whole section.

### 4. Retrieval ranks chunks, not sections

The query runtime retrieves over embedded chunks from the snapshot-scoped queryable corpus.

The retrieved candidate contract carries:

- `doc_id`
- `chunk_id`
- `section_id`
- `heading_path`
- `locator`
- `retrieval_score`
- `retrieval_rank`

This is the clearest implementation proof that the system is chunk-first at retrieval time.

Relevant code:

- `src/doc_forge/readmodels/documents.py`
- `src/doc_forge/query/retrieval.py`
- `src/doc_forge/query/contracts.py`

### 5. Selection preserves section linkage

After retrieval, the selection stage can optionally add adjacent neighbor chunks, but only when they remain in the same document group and, when possible, the same section.

Evidence and citation rendering then preserve:

- document id
- document title
- chunk text snippet
- `section_id`
- `heading_path`
- page label
- chunk id
- locator / passage anchor

So even though retrieval is passage-first, the downstream answer path still carries section-aware provenance.

Relevant code:

- `src/doc_forge/query/selection.py`

### 6. Readiness enforces chunk-to-section integrity

The lifecycle readiness check fails a document if chunks are missing valid section linkage.

That is an important implementation guarantee for this slice: section anchoring is not optional metadata bolted on late. It is part of readiness.

Relevant code:

- `src/doc_forge/lifecycle/readiness.py`

## What the current system is actually optimized for

The current design is optimized for:

- dense retrieval over bounded passages,
- provenance-bearing chunks,
- later grouping into evidence sets,
- inspectable citations that still expose section/path information.

It is not optimized for:

- retrieving whole sections as the default unit,
- making section objects themselves the direct retrieval target,
- or using a retrieval contract named explicitly around `section_path`.

This matches the older query-lifecycle design note, which states that passage-first retrieval is the default and that sections remain semantic containers and citation scaffolding.

## Answers to the section-8 questions

### Is the retrieval unit a whole section, a subsection, or a bounded passage inside a section?

Today it is a **bounded passage chunk inside a recovered section**, with small sections sometimes ending up as one chunk.

### When should a section be split into smaller units?

Today a split happens when:

- the chunk would exceed the coarse token limit, or
- a code block is encountered.

### What anchor metadata must every retrieval unit carry?

The current implementation carries at least:

- `chunk_id`
- `doc_id`
- `heading_path`
- optional `section_id`
- optional page span
- optional source offsets

At retrieval time this becomes:

- `doc_id`
- `chunk_id`
- `section_id`
- `heading_path`
- `locator`
- `retrieval_score`
- `retrieval_rank`

### How do retrieval units point back to the document and section path?

They point back through:

- `doc_id`
- `section_id`
- `heading_path`
- page/offset locator metadata

The code uses `heading_path` rather than a separately named `section_path`, but functionally it fills that role.

### Does the existing system already have a chunk model that can be adapted?

Yes. The current `Chunk` and `RetrievedCandidate` contracts already provide most of the needed surface for the first slice.

### Are there current chunking rules that destroy section semantics?

Not by default.

The current chunker preserves section membership and only splits within section boundaries. The main mismatch is not loss of section semantics, but that the retrieval unit is still a passage chunk rather than an explicitly section-level unit.

## Gap against the desired first-slice framing

The walkthrough outline says:

- retrieval units should be section-aware,
- and should not default to arbitrary windows.

The current system already satisfies most of that requirement:

- chunks are section-aware,
- chunks carry section anchors,
- and neighbor expansion stays section-bounded when possible.

But there is still one important mismatch in framing:

- the runtime is **section-aware passage retrieval**
- while the section-8 prompt leans toward **section-first retrieval units unless splitting is necessary**

That is not a catastrophic gap. It is mainly a naming and emphasis gap.

## Concrete result

For current-system truth, the retrieval unit should be described as:

> a provenance-bearing chunk anchored to one recovered section, carrying document identity, heading-path metadata, and a local locator

If this is rewritten into a first-slice contract, the nearest honest contract is:

- `unit_id`
- `document_id`
- `section_id`
- `section_path` or `heading_path`
- `text`
- `token_count`
- optional `page_start`
- optional `page_end`
- optional `source_start_offset`
- optional `source_end_offset`

## Decision for the walkthrough

Record the current system as:

- **keep as is:** chunk-to-section linkage, heading-path provenance, retrieval candidate metadata, readiness enforcement
- **adapt now:** describe the retrieval unit explicitly as a section-aware chunk and normalize `heading_path` versus `section_path` language
- **defer:** any redesign that makes whole sections the default embedded retrieval unit


## Documentation (current)

Here are the key markdown documents that describe the retrieval unit tree and document hierarchy:

**1. [`docs/delivery/workflow.md`](docs/delivery/workflow.md) (The master reference)**
- Look at section **"8.2 Recommended retrieval-unit hierarchy"**. It explicitly defines the intended tree structure as `DOCUMENT -> SECTION -> PASSAGE`.
- It defines a **Section** as a "semantic and structural container" and a **Passage** as the "default retrieval unit" (a chunk). It explains that this hierarchy is essential for "structure-preserving segmentation" and "stable citation surfaces".

**2. [`docs/workstreams/WS-006-query-lifecycle/04_query-lifecycle-requirements-final.md`](docs/workstreams/WS-006-query-lifecycle/04_query-lifecycle-requirements-final.md)**
- This document outlines the requirements for querying and explicitly mandates that retrieval must preserve the hierarchy: `DOCUMENT -> SECTION -> PASSAGE`.
- It also defines the concept of the **"Structure tree"** (Section 6.3) as the "structural representation recovered during the document lifecycle, including headings, sections, paragraphs, lists... and relative ordering."

**3. [`docs/workstreams/WS-004-document-lifecycle/requirements.md`](docs/workstreams/WS-004-document-lifecycle/requirements.md)**
- This document describes how the system actually builds the tree during ingestion.
- See **"R6. Section recovery"**: Requires the pipeline to produce `Section` records that reconstruct parent-child document structure (the tree branches).
- See **"R7. Chunk production"**: Requires the system to produce `Chunk` records (the leaves of the tree) that "preserve document ownership... and carry heading-path context", favoring discourse boundaries over naive splits.

**4. [`docs/workstreams/WS-033-big-clean/08-retrieval-unit-res-1.md`](docs/workstreams/WS-033-big-clean/08-retrieval-unit-res-1.md)**
- The document you initially asked about! This acts as an audit of the current system, confirming that the code actually implements the `DOCUMENT -> SECTION -> CHUNK` tree successfully.
## Tests (current)

The `DOCUMENT -> SECTION -> CHUNK` tree hierarchy is explicitly verified in the test suite:

**1. Constructing the Section Tree: [`tests/stages/test_section_stage.py`](tests/stages/test_section_stage.py)**
The test `test_markdown_section_stage_recovers_parent_child_hierarchy` is specifically designed to prove the section tree is built correctly. It runs the `SectionDerivationService` over a mocked markdown document and verifies that the "Retries" section correctly points to its "Overview" parent (`assert stored[2].parent_section_id == stored[1].section_id`).

**2. Linking Chunks to Sections: [`tests/stages/test_chunk_stage.py`](tests/stages/test_chunk_stage.py)**
The test `test_chunk_stage_persists_chunks_and_marks_document_chunked` proves the next level of the tree. It feeds `Section` models and normalized blocks into the `ChunkingService` and verifies that every chunk produced is strictly linked back to its correct parent section (`assert all(chunk.section_id == f"{doc_id}:section:0" for chunk in stored)`).

**3. Database Integrity Enforcement: [`tests/persistence/test_integrity_constraints.py`](tests/persistence/test_integrity_constraints.py)**
This test file proves that the database physically enforces this hierarchy through constraints:
- `test_section_cannot_reference_parent_from_another_document`: Proves a section's parent must be in the same document.
- `test_chunk_cannot_reference_section_from_another_document`: Proves a chunk cannot accidentally be linked to a section tree from a completely different document.
