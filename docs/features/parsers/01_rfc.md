# RFC: Structural Parser & Distiller

## 1. Problem and Scope
The Structural Parser & Distiller (Phase 1 component 3.2) converts source-specific raw content into canonical, structured text suitable for deterministic downstream segmentation and citation.

### In Scope
- Parse `RawDocument` content into UTF-8 `canonical_text`.
- Extract a hierarchical `structure_tree` with headings and block nodes.
- Preserve and tag structural blocks (paragraphs, lists, tables, code).
- Generate deterministic anchors (`doc_anchor`, `sec_anchor`, `pass_anchor`).
- Emit block ranges that resolve into `canonical_text`.

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
    "...": "..."
  }
}
```

### 2.3 Required Fields
- `doc_id` must match input `doc_id`.
- `canonical_text` must be non-empty when source has textual content.
- `structure_tree.type` must be `doc`.
- Every block leaf in `structure_tree` must include a valid `range`.
- Every section entry must include both `section_path` and `sec_anchor`.
- Every block anchor entry must include `pass_anchor`, `section_path`, and `range`.

## 3. Invariants and Deterministic Ordering
### 3.1 Invariants
1. Determinism: same `content_bytes`, `content_type`, parser version, and parser config must yield identical `ParsedDocument` output.
2. Anchorability: every `sec_anchor` and `pass_anchor` must resolve to a valid section path or text range in the canonical output.
3. Hierarchical integrity: `structure_tree` must be acyclic; each block has exactly one parent.
4. Information preservation: code block text is verbatim-preserved except newline normalization; table header semantics must be preserved.

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

## 5. Success Criteria (Phase 1)
- Robustness: >= 99% of parser-eligible docs produce non-empty `canonical_text`.
- Structure extraction: heading hierarchy is extracted when headings exist.
- Fidelity: table and code blocks are preserved and tagged.
- Determinism: repeat parses produce identical canonical text, ranges, and anchors.

## 6. Non-Goals
- Connector pagination, source API retries, or fetch cursors.
- Segment token sizing or overlap decisions.
- LLM summaries, synthetic questions, or graph extraction.

## 7. Open Decisions
1. HTML conversion backend choice (`markdownify` + parser vs custom traverser).
2. Canonical newline policy details for mixed Windows/Unix inputs.
3. Hash algorithm/version convention exposed in `metadata.parser_version`.

## 8. Change Control
- Any schema or invariant change in this file requires synchronized updates to:
  - `docs/parsers/02_user_stories.md` traceability matrix
  - `docs/parsers/03_design.md` algorithm/tie-breaker sections
  - `docs/parsers/04_workplan.md` acceptance checks
- Backward-incompatible contract changes must include explicit migration notes and version bump rationale.
