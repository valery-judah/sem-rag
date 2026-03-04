# PR5 Design: Hybrid PDF Distillation & Integration

**Context:** Phase 1 component 3.2 (Structural Parser & Distiller) and Hybrid PDF Parsing Pipeline (Stage D).
**Goal:** Implement the distillation of intermediate `ExtractedPdfDocument` into canonical `ParsedDocument` and integrate the hybrid pipeline into `DeterministicParser` behind a feature flag.

## 1. Scope and Touched Files
- **`src/docforge/parsers/models.py`**: Add `enable_hybrid_pdf_pipeline: bool = False` to `ParserConfig`. Add `pdf_pipeline_version` and pipeline-specific metrics to `ParsedDocument` metadata allowed fields (if any validation exists, but it takes `dict[str, Any]`).
- **`src/docforge/parsers/default.py`**: Conditionally route `RawDocument` with `content_type == "application/pdf"` to the new pipeline when the flag is true.
- **`src/docforge/parsers/pdf_hybrid/distill.py`**: Implement the distillation algorithm mapping the intermediate `schema.py` classes to the `models.py` canonical classes.
- **`tests/parsers/pdf_hybrid/test_distill.py`**: Add robust test fixtures and unit tests for the algorithm.
- **`tests/parsers/test_default_parser.py`**: Add integration tests asserting the correct pipeline routing behavior based on the feature flag.

---

## 2. Distillation Algorithm (`distill.py`)

The function `distill_pdf(extracted_doc: ExtractedPdfDocument, config: ParserConfig) -> ParsedDocument` will be responsible for this conversion.

### 2.1 Canonical Text Construction
- Iterate pages sequentially (`sorted(pages, key=lambda p: p.page_idx)`).
- Within each page, iterate blocks sequentially (`sorted(page.blocks, key=lambda b: b.reading_order_key)`).
- Construct `canonical_text` by appending each block's text:
  - Join blocks within a page with `\n\n`.
  - Join pages with `\n\n\f\n\n` (where `\f` is the form-feed character `\x0c`).
- Track the `start` and `end` byte/character offsets of every appended block relative to the `canonical_text` buffer.

### 2.2 Tree Construction (`DocNode`, `HeadingNode`, `BlockNode`)
Instead of re-parsing the constructed text with `BlockTokenizer` (which is designed for unstructured plain text), we will construct the hierarchical `structure_tree` in a single pass while iterating through the structured blocks.
- Maintain a stack starting with a root `DocNode`.
- Map intermediate `BlockType` to `ParserBlockType` where possible.
  - `BlockType.HEADING` -> determine level (count leading `#`, default to 1). Pop the stack until the top `HeadingNode` has `level < current_level`. Push a new `HeadingNode`.
  - `BlockType.CODE` -> create `BlockNode` of type `ParserBlockType.CODE`. Preserve text verbatim (ensure no markdown stripping alters it).
  - `BlockType.TABLE` -> create `BlockNode` of type `ParserBlockType.TABLE`.
  - `BlockType.LIST` -> create `BlockNode` of type `ParserBlockType.LIST`.
  - `BlockType.PARA`, `BlockType.CAPTION`, `BlockType.FOOTER`, `BlockType.HEADER`, `BlockType.UNKNOWN` -> create `BlockNode` of type `ParserBlockType.PARA` (fallback for unknown/auxiliary text, as `models.py` `ParserBlockType` does not natively support headers/footers directly beyond `PARA`).
- Append each block as a child to the top of the stack (`stack[-1].children.append(block)`). Ensure each block node contains its absolute `range` `[start, end)`.

### 2.3 Anchor Map and Determinism
Generate deterministic anchors according to `docs/features/parsers/01_rfc.md`:
- `doc_anchor`: `hashlib.sha256(extracted_doc.doc_id.encode("utf-8")).hexdigest()[:32]`.
- Maintain a running `normalized_section_path` built from the active heading stack (`H1>H2`).
- Deduplicate sibling headings by keeping a dictionary of `heading_text: count` at the current level, appending `_n` if a duplicate is encountered.
- `sec_anchor`: `hash(doc_id + section_path)`.
- Keep track of `block_ordinal_within_section` resetting on every new section.
- `pass_anchor`: `hash(sec_anchor + block_type + ordinal)`.
- Populate `AnchorMap` with all `sections` (`SectionAnchor`) and `blocks` (`BlockAnchor`).

### 2.4 Provenance and Metadata
Populate the resulting `ParsedDocument.metadata`:
- `parser_version`: Pass through from `ParserConfig.parser_version`.
- `pdf_pipeline_version`: Taken from `extracted_doc.pipeline.pipeline_version`.
- `selected_engine_counts`: Compute frequencies of `marker` vs `mineru` selections across all pages.
- `engine_runs`: Summarize engine statuses from `extracted_doc.engine_runs`.
- Page placeholders (`BlockType.UNKNOWN` representing unparseable pages) will contribute `canonical_text` like `[UNPARSEABLE PAGE N]` and will be parsed as standard `PARA` blocks, fulfilling the "best-effort" fail-safe requirement.

---

## 3. Integration into Default Parser (`default.py`)

### 3.1 Feature Flag
Update `ParserConfig` (in `src/docforge/parsers/models.py`) to include:
```python
class ParserConfig(StrictModel):
    parser_version: str
    blank_line_collapse: int = 2
    enable_hybrid_pdf_pipeline: bool = False  # Feature flag
```

### 3.2 Routing Logic
In `src/docforge/parsers/default.py` (`DeterministicParser.parse()`):
```python
def parse(self, doc: RawDocument) -> ParsedDocument:
    # 1. Routing check
    if doc.content_type == "application/pdf" and self.config.enable_hybrid_pdf_pipeline:
        # Route to the hybrid pipeline
        # pseudo-code:
        # extracted_doc = run_pdf_pipeline(doc, self.config)
        # return distill_pdf(extracted_doc, self.config)
        ...

    # 2. Legacy fallback
    content_bytes = self._materialize_content(doc)
    canon = canonicalize(content_bytes, doc.content_type, self.config.blank_line_collapse)
    ...
```
*Note: The actual entry point function for `run_pdf_pipeline` will coordinate parallel engine execution and intermediate assembly.*

---

## 4. Testing Plan

### 4.1 Fixtures (`tests/parsers/pdf_hybrid/fixtures/`)
Add static JSON fixtures representing valid `ExtractedPdfDocument` dumps for:
1. `digital_born.json`: Text-heavy, multiple block types (headings, paras, lists).
2. `scan_heavy.json`: Pages falling back to OCR/vision extraction, possibly empty pages triggering placeholders.
3. `mixed_layout.json`: Contains multi-column content, tables, and code snippets, demonstrating `reading_order_key` stability and duplicate heading deduplication.

### 4.2 Integration & Unit Tests
- **`test_distill.py`**:
  - Test `distill_pdf()` correctly concatenates text with inter-page separators.
  - Test hierarchical tree building correctly captures nesting and calculates valid, monotonically increasing string ranges.
  - Test anchors are deterministic and don't change across runs for the same fixture.
- **`test_default_parser.py`**:
  - Test `DeterministicParser` correctly branches to hybrid pipeline when flag is True and content is PDF.
  - Test it correctly falls back to legacy `canonicalize()` when flag is False, even for PDFs.
