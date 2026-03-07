# Design: Structural Parser & Distiller

## 1. Design Goals
- Implement parser behavior that satisfies the normative contract in [01_rfc.md](./01_rfc.md).
- Keep parser deterministic under fixed input bytes + parser version/config.
- Preserve structural fidelity for headings, tables, lists, and code blocks.
- Emit ranges and anchors that downstream components can trust without repair logic.
- Make anchor completeness and degraded-output state explicit in metadata instead of leaving them implicit.

## 2. Data Flow
1. Receive `RawDocument` from connector output.
2. Canonicalize source format to internal strict CommonMark + GFM tables text (`canonical_text`).
3. Parse canonical text to AST.
4. Build `structure_tree` using heading-aware stack traversal.
5. Compute block `range` indices against final canonical text.
6. Generate `doc_anchor`, `sec_anchor`, `pass_anchor` deterministically.
7. Derive truthful parser metadata, including anchor-completeness and degraded-output fields.
8. Return `ParsedDocument`.

## 3. Algorithms and Tie-Breakers

### 3.1 Canonicalization by `content_type`
- `text/markdown`: parse directly with normalization pass to ensure strict CommonMark + GFM tables compliance.
- `text/html`: convert to CommonMark + GFM tables using a robust, deterministic library (e.g., `beautifulsoup4` or `markdownify`), preserving tables/code blocks.
- `text/plain`: wrap into paragraph/list-compatible canonical form.
- Other textual types (`text/*`): route through deterministic plain-text normalization.
- `application/pdf`:
  - when the hybrid PDF pipeline is enabled and succeeds, distill PDF output into the canonical parser contract
  - otherwise emit the parser's deterministic degraded-output form
- Unsupported non-textual types (`application/octet-stream`, unknown binary): emit deterministic degraded output.

### 3.1a Metadata contract

Every `ParsedDocument.metadata` must include:
- `parser_version`
- `content_type`
- `has_textual_content`
- `detected_content_family`
- `canonicalization_warnings`
- `anchor_completeness`
- `degraded_output`
- `degraded_reason`

Additional PDF-path metadata may include:
- `pdf_hybrid_pipeline_fallback`
- `pdf_pipeline_version`
- `selected_engine_counts`
- `engine_runs`

The implementation should derive these fields from actual output state, not intended parser capability.

### 3.2 AST parsing and tree construction
- Use a deterministic AST parser configuration (stable options and version pin).
- Maintain a heading stack rooted at `doc`. The `doc` node inherently maps to the document. Its title is derived from `RawDocument.metadata.title` if available; otherwise, it defaults to the `doc_id` or a generic placeholder (e.g., `'Untitled Document'`). Initial blocks before the first heading attach directly to this root.
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
- UTF-8 decode policy for textual inputs:
  - decode with `errors="replace"` so canonicalization is always valid UTF-8 and deterministic.

### 3.4 Duplicate heading policy
- Generate normalized section path material from heading lineage.
- If duplicate sibling headings collide after normalization, append deterministic ordinal suffix (`_0`, `_1`, ...).
- Use resulting path material for `sec_anchor` derivation.

### 3.5 Range calculation strategy
- Compute ranges after canonical text is finalized.
- Track spans in one pass over canonical block serialization.
- Emit `[start, end]` with `0 <= start < end <= len(canonical_text)` for non-empty blocks.
- Empty blocks (e.g., paragraphs containing only whitespace) MUST be discarded. All emitted blocks must have length > 0.

### 3.6 Anchor generation
- `doc_anchor = hash(doc_id)`
- `sec_anchor = hash(doc_id + normalized_section_path_with_ordinal)`
- `pass_anchor = hash(sec_anchor + block_type + block_ordinal_within_section)`
- Hash algorithm and parser version are encoded in parser metadata for reproducibility.

### 3.7 Anchor completeness states

The parser has two valid output profiles:

- `anchor_completeness=document_only`
  - always emit `doc_anchor`
  - emit `anchors.sections=[]`
  - emit `anchors.blocks=[]`
  - use this transitional state when canonical text and structure are available but section/block anchor generation is not yet implemented for that path
- `anchor_completeness=full`
  - emit `doc_anchor`
  - emit exhaustive `anchors.sections`
  - emit exhaustive `anchors.blocks`

The parser must not claim `full` while omitting any emitted section or block from the anchor maps.

For the current repo shape:
- default non-PDF parsing is still in the `document_only` profile
- the PDF distillation path is the target reference for `full`

## 4. Edge-Case Handling
- Missing headings: attach initial blocks to root node.
- Skipped heading levels: keep valid tree without synthesizing missing levels.
- Malformed tables: preserve recoverable textual content. A table is considered malformed if row column counts vary by more than 50% from the header. In such cases, preserve text sequentially as paragraph fallbacks separated by spaces.
- Nested/escaped code fences: treat outer parsed fence as structural boundary and preserve interior text.
- Empty/near-empty input: emit well-formed deterministic degraded output with root tree and truthful metadata.
- Unsupported content type: emit deterministic degraded output instead of raising solely because the content type is unsupported.
- PDF hybrid failure under an enabled fallback path: preserve determinism by reusing the already materialized bytes and emitting degraded output if no textual fallback is available.

## 5. Tradeoff Decisions
- CommonMark + GFM tables canonical representation:
  - Pros: unified downstream parsing path, formal grammar contract, and easier human inspection.
  - Cons: external dependency needed for HTML conversion (e.g., `beautifulsoup4`/`markdownify`) rather than pure stdlib.
- Stack-based heading tree build:
  - Pros: O(n) behavior and deterministic parent selection.
  - Cons: requires strict parser token ordering assumptions.
- Table fallback to paragraph text:
  - Pros: avoids parse crashes and data loss.
  - Cons: may reduce structural precision for malformed sources.
- Explicit anchor-completeness metadata:
  - Pros: makes the current non-PDF parser boundary truthful and gives downstream code a stable feature-detection hook.
  - Cons: requires a later implementation slice to graduate textual parsing from `document_only` to `full`.

## 6. Observability
Emit parser-stage events aligned with Phase 1 vocabulary:
- `DocParsed(doc_id, content_type, parser_version, duration_ms, section_count, block_count)`
- `PipelineError(stage="Parse", doc_id, error_class)`

Recommended event payload fields (for `DocParsed` and potentially debug logs):
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
- Full section/block anchor generation for the non-PDF parser path is deferred until the follow-on parser enforcement slice.
