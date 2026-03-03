# RFC: Structural Parsers

## 1. Problem and Scope
Define deterministic parser contracts that convert raw internal docs into canonical, anchorable, hierarchical retrieval units consumable by downstream Phase 1 components.

### In Scope
- Canonicalization for `text/plain`, `text/markdown`, `text/html`, `application/pdf`
- Structure tree extraction (headings/lists/tables/code/paragraphs)
- Anchor generation for document/section/block-passage
- Segmentation into `SECTION` and `PASSAGE`
- Deterministic ordering/ID rules and contract validation

### Out of Scope
- Connector source crawling/listing logic
- Augmentor prompt tuning/content policy
- Online retrieval/index serving behavior
- Runtime orchestration/retries/rollout strategy

## 2. Normative Contracts
### 2.1 Input Schema
```json
{
  "doc_id": "string",
  "source": "string",
  "source_ref": "string",
  "url": "string",
  "content_bytes": "bytes",
  "content_type": "text/plain|text/markdown|text/html|application/pdf",
  "metadata": {"title": "string"},
  "acl_scope": {"...": "opaque"},
  "timestamps": {"created_at": "timestamp", "updated_at": "timestamp"}
}
```

### 2.2 Output Schema
```json
{
  "doc_id": "string",
  "title": "string",
  "canonical_text": "string",
  "structure_tree": {"type": "doc", "children": []},
  "anchors": {
    "doc": "anchor_ref",
    "sections": [{"path": "H1>H2", "anchor": "anchor_ref"}],
    "blocks": [{"type": "table|code|para", "anchor": "anchor_ref", "range": [0, 1200]}]
  },
  "segments": [
    {
      "segment_id": "string",
      "type": "SECTION|PASSAGE",
      "parent_id": "string|null",
      "section_path": "H1>H2",
      "anchor": "anchor_ref",
      "text": "string",
      "token_count": 0,
      "metadata": {"block_types": ["para"]}
    }
  ]
}
```

### 2.3 Required Fields
- Input required: `doc_id`, `content_bytes`, `content_type`, `timestamps.updated_at`
- Parse required: `canonical_text`, `structure_tree`, `anchors.doc`
- Segment required: `segment_id`, `doc_id`, `type`, `anchor`, `text`, `token_count`

## 3. Invariants and Deterministic Ordering
### 3.1 Invariants
1. For identical input bytes + parser config + code version, canonical text is stable.
2. Every section/block/segment anchor resolves to the source document context.
3. Segment graph is a tree-shaped DAG (no cycles).
4. `segment_id` is stable within an unchanged document version.

### 3.2 Ordering Rules
- Preserve original heading/document order as primary sequence.
- Preserve block order within each section.
- When ties occur (equal offsets), order by block kind priority: heading, paragraph, list, table, code.
- Segment emission order follows section order then in-section passage order.

## 4. Identity / Anchor Policy
- `doc_anchor` derived from stable source doc reference.
- `sec_anchor` derived from normalized section path with collision suffixing (`-2`, `-3`, ...).
- `pass_anchor` derived from section anchor + normalized byte/token offset range.
- Anchor generation must be deterministic and reversible to document context.

## 5. Success Criteria
- Parser output meets schema contracts and invariants for all supported content types.
- Re-running parser on fixed fixtures yields stable outputs.
- Section/table/code handling preserves citation-worthy provenance.

## 6. Non-Goals
- No ranking/scoring behavior changes.
- No guarantees about cross-version ID stability if parser algorithm changes.

## 7. Open Decisions
1. PDF backend choice and pinned version policy.
2. Tokenizer source for token counting and long-term version pinning.
3. Whether table row-group splitting repeats full header or projected header subset.

## 8. Change Control
- Contract changes require updates to:
  - `01_rfc.md` (normative)
  - `02_user_stories.md` traceability
  - `03_design.md` algorithms
  - `04_workplan.md` acceptance criteria/tests
