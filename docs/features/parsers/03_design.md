# Design: Structural Parsers

## 1. Design Goals
- Deterministic canonicalization and segmentation for fixed inputs.
- High-fidelity structure extraction for citation-quality retrieval units.
- Clear separation of parser stages for testability and incremental delivery.

## 2. Data Flow
1. Accept `RawDocument`.
2. Select canonicalizer by `content_type`.
3. Normalize to UTF-8 canonical text + coarse blocks.
4. Build structure tree with heading-scoped grouping.
5. Generate `doc/section/block` anchors.
6. Emit `SECTION` segments from heading scopes.
7. Emit `PASSAGE` segments with token-budget policy.
8. Write parser artifacts for downstream augmentor/indexing.

## 3. Algorithms and Tie-Breakers
### 3.1 Canonicalization
- Apply newline normalization (`CRLF` -> `LF`) globally.
- Preserve code-block verbatim body except newline normalization.
- For tables, serialize with explicit header row and stable column order.

### 3.2 Structure extraction
- Parse headings into a stack by level.
- Attach non-heading blocks to current section context.
- If no heading exists, create implicit root section.

### 3.3 Anchor generation
- Normalize slug input (lowercase, trim, collapse separators).
- Build section anchor from full path (not leaf-only title).
- Resolve collisions deterministically via monotonic suffixes.

### 3.4 Segmentation
- SECTION segment: one per structural section node.
- PASSAGE segmentation target: 300–800 tokens, overlap 0–15%.
- Prefer semantic boundaries in order: paragraph -> list item -> table row-group -> sentence.
- Code splitting priority: function/class boundaries -> blank-line groups -> hard token cut.

## 4. Edge-Case Handling
- Empty/whitespace docs: emit minimal parse artifact with doc anchor.
- Unknown `content_type`: typed parse error with actionable reason.
- Deep heading skips (e.g., H1 -> H4): preserve as-given; do not auto-correct levels.
- Duplicate headings: path-based plus suffix policy ensures uniqueness.

## 5. Tradeoff Decisions
- Prefer deterministic heuristics over model-assisted parsing in MVP.
- Prefer preserving source order over aggressive normalization for readability.
- Favor larger cohesive blocks (tables/code) until token limits force splitting.

## 6. Observability
- Events:
  - `parser.canonicalized`
  - `parser.structured`
  - `parser.segmented`
  - `parser.failed`
- Payload fields:
  - `doc_id`, `content_type`, `parser_profile`, `duration_ms`
  - `section_count`, `passage_count`, `anchor_count`
  - `error_code`/`error_reason` on failures

## 7. Performance and Complexity Notes
- Single-pass structure extraction should be O(n) in block count.
- Segmentation complexity is O(n) with bounded local split heuristics.
- Memory footprint dominated by canonical text + structure tree for one document.

## 8. Limitations and Deferred Items
- OCR quality handling for scanned PDFs is deferred.
- Advanced table semantics (merged cells/spans) are best-effort in MVP.
- Language-specific code AST splitting is deferred; heuristic boundaries first.
