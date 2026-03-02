# Context & Spec: Hierarchical Segmentation (TDD-friendly)

---
feature: hierarchical_segmentation
phase: phase1_knowledge_representation
component: retrieval.segmenter
owner: retrieval
upstream:
  - structural_parser_distiller
downstream:
  - embedder
  - llm_augmentor
  - graph_extractor
  - index_publisher
entrypoints:
  - python: retrieval/segmenter.py:segment_document
fixtures:
  - docs/segmentation/00_context.md#example:input:minimal
  - docs/segmentation/00_context.md#example:output:minimal_normalized
test_command: pytest -k segmentation
---

## 0) What this module does (pipeline placement)

**Upstream:** consumes parser/distiller outputs:
- `canonical_text` (single canonical string)
- `structure_tree` (document structure; headings, blocks, etc.)
- `anchors` (stable references for doc/sections/blocks; may include ranges into canonical_text)

**Downstream:** produces hierarchical units for indexing and retrieval-time grounding:
- `SECTION` nodes: hierarchy/metadata/navigation (parents of passages)
- `PASSAGE` nodes: retrievable spans (anchored back to canonical text)

**Module boundary:** the segmenter is responsible for **hierarchy + passage boundaries + IDs + offsets/anchors + ordering**.
It is *not* responsible for parsing or canonicalization.

---

## 1) Boundary contract (frozen)

### 1.1 Input contract (from structural parser/distiller)

#### Required fields
- `doc_id: str`
- `doc_version_id: str`
- `canonical_text: str`
- `structure_tree: object` (strict tree; no cycles)
- `anchors: object|list` (see anchor notes below)

#### Input schema (representative)
```json
{
  "doc_id": "string",
  "doc_version_id": "string",
  "title": "string|null",
  "canonical_text": "string",
  "structure_tree": { "node_type": "doc", "children": [ /* ... */ ] },
  "anchors": {
    "doc": { "ref": "anchor_ref" },
    "sections": [{ "path": "H1>H2", "ref": "anchor_ref" }],
    "blocks": [
      {
        "block_type": "table|code|para|list|heading",
        "ref": "anchor_ref",
        "range": [0, 1200]
      }
    ]
  },
  "metadata": {}
}
```

#### Anchor notes (input)
- `anchors.blocks[*].range` (if present) is interpreted as **[start_char_offset, end_char_offset]** into `canonical_text`.
- If upstream does **not** provide block ranges, the segmenter must still compute offsets deterministically from `canonical_text` + structural node text.

---

### 1.2 Output contract (segment nodes)

#### Output shape
The segmenter returns a single ordered list:
- `SECTION` nodes first (pre-order traversal), then
- `PASSAGE` nodes in document reading order within each section.

#### Required fields (minimum)
- `segment_id: str` *(deterministic)*
- `doc_id: str`
- `doc_version_id: str`
- `segment_type: "SECTION"|"PASSAGE"`
- `parent_id: str|null` *(PASSAGE must have a SECTION parent)*
- `section_path: str` *(stable path like `H1>H2`)*
- `anchor_ref: str` *(stable reference; see below)*
- `start_char_offset: int` *(PASSAGE required; SECTION optional)*
- `end_char_offset: int` *(PASSAGE required; SECTION optional)*
- `section_ordinal: int` *(SECTION required)*
- `passage_ordinal: int|null` *(PASSAGE required; SECTION null)*
- `token_count: int`
- `text: str` *(for indexing; tests may snapshot only hashes)*

#### Output schema (representative)
```json
{
  "segments": [
    {
      "segment_id": "string",
      "doc_id": "string",
      "doc_version_id": "string",
      "segment_type": "SECTION|PASSAGE",
      "parent_id": "string|null",
      "section_path": "H1>H2",
      "anchor_ref": "string",
      "start_char_offset": 0,
      "end_char_offset": 500,
      "section_ordinal": 0,
      "passage_ordinal": 0,
      "token_count": 120,
      "text": "string",
      "metadata": {
        "block_types": ["para"],
        "is_special": false,
        "special_type": null,
        "split_reason": "heading|paragraph|max_tokens|table|code|merge_small|overlap",
        "overlap_from_segment_id": null,
        "overlap_token_count": 0
      }
    }
  ]
}
```

#### Anchor notes (output)
- `anchor_ref` is required for every segment.
  - Prefer upstream `ref` when available.
  - If upstream provides only ranges, use a deterministic fallback ref: `range:{start}:{end}`.
- Offsets are the canonical truth for resolution tests (they must map into `canonical_text`).

---

## 2) Determinism + snapshot normalization (frozen)

### 2.1 Deterministic ordering
- **SECTION order:** pre-order traversal of `structure_tree` headings.
- **PASSAGE order within a SECTION:** increasing `start_char_offset`, tie-break by `end_char_offset`, tie-break by `block_types` stable order.

### 2.2 Segment identity (segment_id)
`segment_id` MUST be deterministic for the same `(doc_id, doc_version_id, inputs, config)`.

Minimum stable inputs to hash:
- `doc_id`, `doc_version_id`
- `segment_type`
- `section_path`
- `anchor signature` *(prefer `anchor_ref`; else use offsets)*
- `start_char_offset`, `end_char_offset`
- `config_hash` (see below)

**Config hash:** stable hash of all segmentation-affecting configuration (tokenizer name/version, min/max tokens, overlap, special splitting toggles, etc).

> Tests assert determinism, not a specific hashing algorithm. The only hard requirement is that the chosen algorithm is stable and documented.

### 2.3 Snapshot record (to keep snapshots stable)
Golden snapshots SHOULD store a normalized record per segment:
- `segment_id`
- `segment_type`
- `parent_id`
- `section_path`
- `section_ordinal`
- `passage_ordinal`
- `start_char_offset`, `end_char_offset`
- `token_count`
- `is_special`, `special_type`
- `split_reason`
- `text_hash = sha256(text)` (instead of full text)

This avoids brittle diffs while still catching meaningful changes.

---

## 3) Invariants (CI-protected)

These are non-negotiable. CI gates must fail on violation.

1) **Strict hierarchy:** segments form a strict tree; `PASSAGE` has exactly one SECTION parent; no cycles.
2) **Anchorability:** offsets are in-bounds and resolve back to the intended `canonical_text` span.
3) **No empty passages:** passage `text.strip()` is never empty.
4) **Determinism:** same inputs + config ⇒ identical normalized output (including ordering, IDs, offsets).
5) **Bounded sizing (with explicit exceptions):**
   - PASSAGE tokens should fall within `[passage_tokens_min, passage_tokens_max]`
   - Exceptions are only for explicitly marked `is_special=true` segments.

---

## 4) Special segments policy (frozen enough for tests)

### Tables
- Default: preserve tables as `is_special=true`, `special_type="table"` if they cannot be safely chunked.
- If table splitting is enabled: split by row groups and **repeat header row** in each emitted passage.

### Code blocks
- Default: preserve code blocks as `is_special=true`, `special_type="code"` if they cannot be safely chunked.
- If code splitting is enabled: split at deterministic logical boundaries (e.g., function/class boundaries or blank-line groups), never mid-token.

---

## 5) Quality gates (CI thresholds)

- `no_empty_segments`: 0 empty PASSAGE texts
- `offsets_in_bounds`: all PASSAGE offsets within `[0, len(canonical_text)]` and `start < end`
- `required_fields_present`: all required fields exist and types match
- `strict_tree`: no cycles; PASSAGE has exactly one SECTION parent
- `determinism_snapshot`: normalized snapshot matches golden output
- `table_header_repetition`: if table splitting enabled, header repetition is enforced
- `mid_sentence_split_rate_lt`: < 0.5% for non-special segments (measured on golden corpus)

---

## 6) Golden examples (runnable fixtures)

### Example: minimal input
```json example:input:minimal
{
  "doc_id": "doc_123",
  "doc_version_id": "v1",
  "title": "Example",
  "canonical_text": "Introduction\n\nThis is the first paragraph of the introduction.\n\nHere is the second paragraph.",
  "structure_tree": {
    "node_type": "doc",
    "children": [
      {
        "node_type": "heading",
        "level": 1,
        "text": "Introduction",
        "children": [
          { "node_type": "paragraph", "text": "This is the first paragraph of the introduction." },
          { "node_type": "paragraph", "text": "Here is the second paragraph." }
        ]
      }
    ]
  },
  "anchors": {
    "doc": { "ref": "a_doc" },
    "sections": [{ "path": "H1", "ref": "a_sec_1" }],
    "blocks": [
      { "block_type": "paragraph", "ref": "a_p1", "range": [13, 61] },
      { "block_type": "paragraph", "ref": "a_p2", "range": [63, 92] }
    ]
  },
  "metadata": {}
}
```

### Example: expected normalized output (minimal)
Notes:
- IDs are placeholders here; snapshot tests should validate determinism via the implementation’s ID function.
- Offsets MUST be exact and anchor-resolvable.
```json example:output:minimal_normalized
[
  {
    "segment_type": "SECTION",
    "parent_id": null,
    "section_path": "H1",
    "section_ordinal": 0,
    "passage_ordinal": null,
    "start_char_offset": null,
    "end_char_offset": null
  },
  {
    "segment_type": "PASSAGE",
    "parent_id": "<SECTION_ID>",
    "section_path": "H1",
    "section_ordinal": 0,
    "passage_ordinal": 0,
    "start_char_offset": 13,
    "end_char_offset": 61,
    "metadata": { "block_types": ["paragraph"], "is_special": false }
  },
  {
    "segment_type": "PASSAGE",
    "parent_id": "<SECTION_ID>",
    "section_path": "H1",
    "section_ordinal": 0,
    "passage_ordinal": 1,
    "start_char_offset": 63,
    "end_char_offset": 92,
    "metadata": { "block_types": ["paragraph"], "is_special": false }
  }
]
```

---

## 7) Test map (TDD-first)

| Contract / Invariant | Test file | What it asserts |
|---|---|---|
| Required fields + types | `tests/segmentation/test_schema_contract.py` | Output conforms to boundary contract (fields present, types correct) |
| Strict tree | `tests/segmentation/test_hierarchy.py` | No cycles; PASSAGE has exactly one SECTION parent; ordinals monotonic |
| Offsets + anchor resolution | `tests/segmentation/test_offsets_and_resolution.py` | Offsets in bounds; extracted span equals segment text; anchor_ref present |
| Determinism | `tests/segmentation/test_determinism_snapshot.py` | Two runs identical after normalization; snapshot matches golden |
| Table rules (if enabled) | `tests/segmentation/test_tables.py` | Header repetition; stable splitting boundaries |
| Code rules (if enabled) | `tests/segmentation/test_code_blocks.py` | Deterministic logical splits; never mid-token |
| Merge small + overlap | `tests/segmentation/test_merge_and_overlap.py` | Policy correctness + provenance fields |

**Run:** `pytest -k segmentation`

---

## 8) Known gaps / dependencies (keep short)

- Depends on upstream parser providing stable `canonical_text` and consistent structure traversal.
- If upstream anchors do not include ranges, the segmenter must compute offsets deterministically (and document the method in `03_design.md`).
- Tokenizer choice affects `token_count` and bounded sizing; must be captured in `config_hash`.
