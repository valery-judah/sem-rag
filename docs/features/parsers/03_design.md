# Design: Structural Parser & Distiller

## 1. Design Goals
- Implement parser behavior that satisfies the normative contract in [01_rfc.md](./01_rfc.md).
- Keep parser deterministic under fixed input bytes + parser version/config.
- Preserve structural fidelity for headings, tables, lists, and code blocks.
- Emit ranges and anchors that downstream components can trust without repair logic.

## 2. Data Flow
1. Receive `RawDocument` from connector output.
2. Canonicalize source format to internal markdown-like text (`canonical_text`).
3. Parse canonical text to AST.
4. Build `structure_tree` using heading-aware stack traversal.
5. Compute block `range` indices against final canonical text.
6. Generate `doc_anchor`, `sec_anchor`, `pass_anchor` deterministically.
7. Return `ParsedDocument` with parser metadata.

## 3. Algorithms and Tie-Breakers

### 3.1 Canonicalization by `content_type`
- `text/markdown`: parse directly with normalization pass.
- `text/html`: convert to markdown-like representation, preserving tables/code blocks.
- `text/plain`: wrap into paragraph/list-compatible canonical form.
- Other textual types: route through best-effort text extraction policy; parser remains deterministic for the chosen policy.

### 3.2 AST parsing and tree construction
- Use a deterministic AST parser configuration (stable options and version pin).
- Maintain a heading stack rooted at `doc`.
- For each heading node:
  - pop while top heading level is greater than or equal to incoming level
  - attach heading under resulting parent
  - push heading node
- For each non-heading block:
  - attach to current stack top (or root if stack contains only root)

### 3.3 Deterministic normalization rules
- Outside code blocks:
  - normalize line endings
  - collapse repeated blank lines according to config
  - trim trailing whitespace where policy allows
- Inside code blocks:
  - preserve verbatim text and indentation
  - do not collapse internal whitespace

### 3.4 Duplicate heading policy
- Generate normalized section path material from heading lineage.
- If duplicate sibling headings collide after normalization, append deterministic ordinal suffix (`_0`, `_1`, ...).
- Use resulting path material for `sec_anchor` derivation.

### 3.5 Range calculation strategy
- Compute ranges after canonical text is finalized.
- Track spans in one pass over canonical block serialization.
- Emit `[start, end]` with `0 <= start < end <= len(canonical_text)` for non-empty blocks.
- For empty blocks (if representable), enforce deterministic zero-length policy.

### 3.6 Anchor generation
- `doc_anchor = hash(doc_id)`
- `sec_anchor = hash(doc_id + normalized_section_path_with_ordinal)`
- `pass_anchor = hash(sec_anchor + block_type + block_ordinal_within_section)`
- Hash algorithm and parser version are encoded in parser metadata for reproducibility.

## 4. Edge-Case Handling
- Missing headings: attach initial blocks to root node.
- Skipped heading levels: keep valid tree without synthesizing missing levels.
- Malformed tables: preserve recoverable textual content; mark as paragraph fallback when table semantics cannot be trusted.
- Nested/escaped code fences: treat outer parsed fence as structural boundary and preserve interior text.
- Empty/near-empty input: emit well-formed deterministic document with root tree and metadata.

## 5. Tradeoff Decisions
- Markdown-like canonical representation:
  - Pros: unified downstream parsing path and easier human inspection.
  - Cons: HTML edge cases may need fallback handling.
- Stack-based heading tree build:
  - Pros: O(n) behavior and deterministic parent selection.
  - Cons: requires strict parser token ordering assumptions.
- Table fallback to paragraph text:
  - Pros: avoids parse crashes and data loss.
  - Cons: may reduce structural precision for malformed sources.

## 6. Observability
Emit parser-stage events aligned with Phase 1 vocabulary:
- `DocParsed(doc_id, anchors_count, structure_nodes)`
- `PipelineError(stage="Parse", doc_id, error_class)`

Recommended event payload fields:
- `doc_id`
- `content_type`
- `parser_version`
- `canonical_text_len`
- `section_count`
- `block_count`
- `table_count`
- `code_count`
- `duration_ms`

## 7. Performance and Complexity Notes
- Expected asymptotic complexity is linear in AST node count and canonical text length.
- Memory footprint is dominated by canonical text + tree representation.
- Large-document behavior should prioritize streaming conversion where feasible, while preserving deterministic output semantics.

## 8. Limitations and Deferred Items
- OCR/image-heavy PDFs are deferred beyond parser core scope.
- Cross-document entity normalization is out of scope.
- Token-aware passage optimization belongs to segmenter (component 3.3), not parser.
