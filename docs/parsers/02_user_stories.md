# User Stories: Structural Parser & Distiller

## Overview
As a pipeline operator and downstream segmenter, I need raw documents converted into a unified, cleanly structured canonical format with explicitly extracted heading hierarchies, tables, code blocks, and precise character offsets, so that semantic units can be chunked accurately without losing structural context or verifiable anchors.

## Acceptance Criteria (Testable Checks)

### AC1: Format Canonicalization
- **Given** a `RawDocument` with `content_type` of `text/html` or `text/markdown`,
- **When** passed through the parser,
- **Then** the output `canonical_text` must be valid UTF-8.
- **And** all textual content from the source must be present, with formatting normalized to a standard representation (e.g., Markdown-like headers, lists, and paragraphs).

### AC2: Heading Hierarchy Extraction
- **Given** a document containing hierarchical headings (e.g., H1, H2, H3),
- **When** the structure tree is generated,
- **Then** the `structure_tree` must accurately reflect the parent-child relationships of the headings.
- **And** block elements (paragraphs, tables) must be attached as leaves to the most recently declared heading in the document flow.

### AC3: Table Preservation
- **Given** a document containing an HTML or Markdown table,
- **When** the parser processes the table,
- **Then** the `structure_tree` must contain a block node of type `table`.
- **And** the serialization within `canonical_text` must retain the semantic structure of rows and header columns (e.g., a Markdown table with a header separator `|---|`).

### AC4: Code Block Preservation
- **Given** a document containing a fenced code block with formatting and indentation,
- **When** the parser processes the code block,
- **Then** the `structure_tree` must contain a block node of type `code`.
- **And** the `language` tag (if present) must be extracted into the node's attributes.
- **And** the exact whitespace, newlines, and indentation must be preserved verbatim in the `canonical_text`.

### AC5: Deterministic Anchor Generation
- **Given** a document and its generated structure tree,
- **When** anchors are generated for sections and blocks,
- **Then** the `doc_anchor` must be a stable hash derived from the source `doc_id`.
- **And** `sec_anchor` strings must be a stable hash of the document ID and the section's path (e.g., `H1>H2`).
- **And** processing the exact same document twice must result in identical anchor hashes.

### AC6: Precise Character Offsets
- **Given** the generated `canonical_text` and the `structure_tree`,
- **When** evaluating the `range` attribute of any block node,
- **Then** extracting the substring `canonical_text[range[0]:range[1]]` must exactly yield the textual content of that block.

## Quality Gates
- **Success Rate:** $\ge 99\%$ of a diverse golden corpus (HTML, Markdown, Plain Text) parses successfully without unhandled exceptions.
- **Empty Output Prevention:** 0 instances of completely empty `canonical_text` for documents known to have content.
- **Coverage:** 100% test coverage for the specialized extraction logic handling tables and code blocks.
