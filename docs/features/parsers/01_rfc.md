# RFC: Structural Parser & Distiller

## 1. Problem and Scope
The Structural Parser & Distiller (Phase 1 component 3.2) converts source-specific raw content into canonical, structured text suitable for deterministic downstream segmentation and citation.

### In Scope
- Parse `RawDocument` content into UTF-8 `canonical_text`.
- Extract a hierarchical `structure_tree` with headings and block nodes.
- Preserve and tag structural blocks (paragraphs, lists, tables, code).
- Generate deterministic parser anchors with explicit completeness signaling.
- Emit block ranges that resolve into `canonical_text`.
- Define parser metadata that makes supported-content and degraded-output behavior explicit.

### Out of Scope
- Fetching content from source systems (component 3.1).
- Passage sizing/chunking policy (component 3.3).
- LLM-based parsing or extraction.
- OCR/image transcription policy beyond what upstream content extraction already provides.

## 2. Normative Contracts
This file is the single authoritative contract for parser inputs/outputs and invariants in `docs/parsers/`.

### 2.1 Input Schema (`RawDocument`)
```json
{
  "doc_id": "string",
  "source": "confluence|gdrive|git|jira|...",
  "source_ref": "string",
  "url": "string",
  "content_bytes": "bytes",
  "content_type": "text/html|text/markdown|application/pdf|text/plain|...",
  "metadata": { "title": "string", "...": "..." },
  "acl_scope": { "...": "opaque" },
  "timestamps": { "created_at": "timestamp", "updated_at": "timestamp" }
}
```

### 2.2 Output Schema (`ParsedDocument`)
```json
{
  "doc_id": "string",
  "title": "string",
  "canonical_text": "string",
  "structure_tree": {
    "type": "doc",
    "children": [
      {
        "type": "heading",
        "level": 1,
        "text": "string",
        "children": [
          {
            "type": "para|list|table|code",
            "range": [0, 120],
            "metadata": { "language": "python" }
          }
        ]
      }
    ]
  },
  "anchors": {
    "doc_anchor": "anchor_ref",
    "sections": [
      {
        "section_path": "H1>H2",
        "sec_anchor": "anchor_ref"
      }
    ],
    "blocks": [
      {
        "type": "para|list|table|code",
        "section_path": "H1>H2",
        "pass_anchor": "anchor_ref",
        "range": [0, 120]
      }
    ]
  },
  "metadata": {
    "parser_version": "string",
    "content_type": "string",
    "has_textual_content": true,
    "detected_content_family": "markdown|html|plain|unsupported",
    "canonicalization_warnings": ["string"],
    "anchor_completeness": "document_only|full",
    "degraded_output": false,
    "degraded_reason": "unsupported_content_type|no_textual_content|pdf_pipeline_unavailable|pdf_pipeline_failed|empty_input|null",
    "...": "..."
  }
}
```

### 2.3 Required Fields
- `doc_id` must match input `doc_id`.
- `title` must use `RawDocument.metadata.title` when it is a non-empty string; otherwise it must fall back to `RawDocument.source_ref`.
- `canonical_text` must be non-empty when `metadata.has_textual_content=true`.
- `structure_tree.type` must be `doc`.
- Every block leaf in `structure_tree` must include a valid `range`.
- `metadata` must include:
  - `parser_version`
  - `content_type`
  - `has_textual_content`
  - `detected_content_family`
  - `canonicalization_warnings`
  - `anchor_completeness`
  - `degraded_output`
- `anchors.doc_anchor` is required for every `ParsedDocument`.
- Every emitted section entry must include both `section_path` and `sec_anchor`.
- Every emitted block anchor entry must include `pass_anchor`, `section_path`, and `range`.

### 2.4 Supported Content-Type Behavior

The parser contract recognizes the following content-type classes:

- Markdown-like textual input:
  - `text/markdown`
  - `text/x-markdown`
- HTML-like textual input:
  - `text/html`
  - `application/xhtml+xml`
- Plain textual input:
  - `text/plain`
  - other `text/*` inputs routed through deterministic plain-text normalization
- PDF input:
  - `application/pdf`
- Unsupported / non-textual input:
  - any other content type

Normative behavior by class:

- Markdown-like, HTML-like, and plain textual inputs must produce a valid `ParsedDocument` with:
  - deterministic `canonical_text`
  - `metadata.has_textual_content=true` when normalized text is non-empty
  - a non-empty `structure_tree` when normalized text is non-empty
- PDF inputs may produce either:
  - a distilled textual `ParsedDocument` from the hybrid PDF path, or
  - a valid degraded `ParsedDocument` when PDF extraction is unavailable or fails within the parser's fallback contract
- Unsupported / non-textual inputs must not crash the parser merely because the type is unsupported. They must produce a valid degraded `ParsedDocument`.

### 2.5 Anchor Completeness Contract

The parser contract allows two anchor-completeness states, recorded in `metadata.anchor_completeness`:

- `document_only`
  - `anchors.doc_anchor` is present
  - `anchors.sections` and `anchors.blocks` may be empty
  - downstream consumers must not assume section/block anchor coverage
- `full`
  - `anchors.doc_anchor` is present
  - `anchors.sections` must cover every emitted logical section
  - `anchors.blocks` must cover every emitted block leaf in document order

For the current parser delivery shape:

- non-PDF textual parsing is allowed to remain `document_only` until section/block anchor generation is implemented for that path
- distilled PDF output is expected to target `full`

### 2.6 Degraded-Output Contract

The parser must prefer returning a valid degraded `ParsedDocument` over raising an exception for deterministic, non-programmer-error scenarios such as:

- unsupported `content_type`
- empty or near-empty normalized text
- PDF hybrid pipeline unavailable within a supported fallback path
- PDF hybrid pipeline failure that falls back to baseline parser behavior

A degraded `ParsedDocument` must satisfy all of the following:

- `metadata.degraded_output=true`
- `metadata.degraded_reason` explains the dominant reason
- `metadata.has_textual_content=false`
- `canonical_text=""`
- `structure_tree` is a valid root `doc` node and may have no children
- `anchors.sections=[]`
- `anchors.blocks=[]`

When the parser produces meaningful textual output, it must set `metadata.degraded_output=false` and `metadata.degraded_reason=null`.

## 3. Invariants and Deterministic Ordering
### 3.1 Invariants
1. Determinism: same `content_bytes`, `content_type`, parser version, and parser config must yield identical `ParsedDocument` output.
2. Anchorability:
   - `doc_anchor` must always be deterministic for a given `doc_id`.
   - When `metadata.anchor_completeness=full`, every `sec_anchor` and `pass_anchor` must resolve to a valid section path or text range in the canonical output.
3. Hierarchical integrity: `structure_tree` must be acyclic; each block has exactly one parent.
4. Information preservation: code block text is verbatim-preserved except newline normalization; table header semantics must be preserved.
5. Metadata truthfulness: `metadata.has_textual_content`, `metadata.anchor_completeness`, and `metadata.degraded_output` must describe the actual output rather than the aspirational parser state.

### 3.2 Ordering Rules
- Section order is document order (top-to-bottom).
- Block order within a section is document order.
- Duplicate section headings under the same parent use deterministic ordinal tie-breakers in normalized path material.

## 4. Anchor and ID Policy
### 4.1 Normalization
- `section_path` format is `H1>H2>...`.
- Heading text is normalized for stable hashing (casefold + trim + canonical whitespace).
- Duplicate sibling headings append `_n` ordinal (`_0`, `_1`, ...).

### 4.2 Anchor Derivation
- `doc_anchor = hash(doc_id)`
- `sec_anchor = hash(doc_id + normalized_section_path)`
- `pass_anchor = hash(sec_anchor + block_type + block_ordinal_within_section)`

`hash(...)` indicates a deterministic stable hash function chosen by implementation and versioned in parser metadata.

### 4.3 Anchor Emission Rules
- `doc_anchor` must always be emitted.
- `sec_anchor` and `pass_anchor` must be emitted only when the parser can satisfy `metadata.anchor_completeness=full`.
- The parser must not emit partial section/block anchor coverage while claiming `full`.
- A document that emits only `doc_anchor` must set `metadata.anchor_completeness=document_only`.

## 5. Success Criteria (Phase 1)
- Robustness: >= 99% of parser-eligible docs produce non-empty `canonical_text`.
- Structure extraction: heading hierarchy is extracted when headings exist.
- Fidelity: table and code blocks are preserved and tagged.
- Determinism: repeat parses produce identical canonical text, ranges, metadata truthfulness, and anchors appropriate to the declared anchor-completeness state.

## 6. Non-Goals
- Connector pagination, source API retries, or fetch cursors.
- Segment token sizing or overlap decisions.
- LLM summaries, synthetic questions, or graph extraction.

## 7. Open Decisions
1. HTML conversion backend choice (`markdownify` + parser vs custom traverser).
2. Canonical newline policy details for mixed Windows/Unix inputs.
3. Hash algorithm/version convention exposed in `metadata.parser_version`.
4. Graduation criteria for moving non-PDF textual parsing from `document_only` to `full`.

## 8. Change Control
- Any schema or invariant change in this file requires synchronized updates to:
  - `docs/parsers/02_user_stories.md` traceability matrix
  - `docs/parsers/03_design.md` algorithm/tie-breaker sections
  - `docs/parsers/04_workplan.md` acceptance checks
- Backward-incompatible contract changes must include explicit migration notes and version bump rationale.
