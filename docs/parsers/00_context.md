# Context: Structural Parser & Distiller

## Pipeline Placement
The Structural Parser & Distiller (Component 3.2) is the second step in the Knowledge Representation Pipeline. 
- **Upstream Dependency:** Source Connectors (Component 3.1) which provide raw, format-specific document content (`RawDocument`).
- **Downstream Dependency:** Hierarchical Segmenter (Component 3.3) which consumes the canonical text and structure tree to produce chunked segments.
- **Module Path:** `src/docforge/parsers/`

## Boundary Contract
### Input Schema (`RawDocument`)
```json
{
  "doc_id": "string",
  "source": "string",
  "content_bytes": "bytes",
  "content_type": "string",
  "metadata": { "title": "string" }
}
```

### Output Schema (`ParsedDocument`)
```json
{
  "doc_id": "string",
  "title": "string",
  "canonical_text": "string",
  "structure_tree": { "type": "doc", "children": [ ... ] },
  "anchors": {
    "doc": "anchor_ref",
    "sections": [{ "path": "H1>H2", "anchor": "anchor_ref" }],
    "blocks": [{ "type": "table|code|para", "anchor": "anchor_ref", "range": [0, 1200] }]
  },
  "metadata": { "...": "..." }
}
```

## Invariants
1. **Determinism:** The same raw bytes and `content_type` must always yield the exact same `ParsedDocument` (identical canonical text, structure tree, and anchors).
2. **Anchorability:** Every generated section and block anchor must resolve to a valid range or path within the source document or canonical text.
3. **Hierarchical Integrity:** The extracted `structure_tree` must form a valid Directed Acyclic Graph (DAG), typically a strict tree of headings, where blocks (paragraphs, tables, code) are leaves attached to their nearest preceding heading.
4. **Information Preservation:** Verbatim text in code blocks and header associations in tables must not be lost or structurally corrupted during canonicalization.

## Golden Examples
### Input (Markdown)
```markdown
# My Project
Here is a description.
## Setup
```python
print("hello")
```
```

### Output
```json
{
  "doc_id": "proj-123",
  "canonical_text": "# My Project\nHere is a description.\n## Setup\n```python\nprint(\"hello\")\n```\n",
  "structure_tree": {
    "type": "doc",
    "children": [
      {
        "type": "heading",
        "level": 1,
        "text": "My Project",
        "children": [
          { "type": "para", "range": [13, 35] },
          {
            "type": "heading",
            "level": 2,
            "text": "Setup",
            "children": [
              { "type": "code", "language": "python", "range": [44, 66] }
            ]
          }
        ]
      }
    ]
  },
  "anchors": {
    "doc": "doc-anchor-hash",
    "sections": [
      { "path": "My Project", "anchor": "sec-anchor-1" },
      { "path": "My Project>Setup", "anchor": "sec-anchor-2" }
    ],
    "blocks": [
      { "type": "para", "anchor": "blk-anchor-1", "range": [13, 35] },
      { "type": "code", "anchor": "blk-anchor-2", "range": [44, 66] }
    ]
  }
}
```

## Test Map
| Invariant | Enforced By | Test Type |
|-----------|-------------|-----------|
| Determinism | `test_parser_snapshot_determinism` | Snapshot |
| Anchorability | `test_anchor_range_resolution` | Property |
| Hierarchical Integrity | `test_structure_tree_acyclic` | Property |
| Table Preservation | `test_markdown_table_headers_preserved` | Unit |
| Code Preservation | `test_code_block_whitespace_preserved` | Unit |
