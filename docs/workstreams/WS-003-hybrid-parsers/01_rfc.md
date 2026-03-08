# RFC: Hybrid PDF Parsing Pipeline (Marker + MinerU Parallel, Intermediate Schema)

**Status:** Draft  
**Owners:** _TBD_  
**Last updated:** 2026-03-03

## 1. Problem statement

`application/pdf` is a high-variance source format: some PDFs are digital-born (rich embedded text), some are scan-heavy (rasterized pages), and many contain complex layouts (multi-column, marginalia, footnotes/citations, tables, figures, equations). Single-engine parsing produces failure modes that are both common and complementary:
- **Catastrophic empty output** for certain pages/documents (engine crash / malformed geometry).
- **Partial empties** (some pages missing).
- **Reading-order corruption** (multi-column, margin notes).
- **Structure loss** (headings/lists/tables collapse to flat text).

We need a deterministic pipeline that:
1) maximizes coverage (non-empty output per page),  
2) preserves stable structure for downstream chunking, and  
3) provides traceability (page + region provenance) for debugging/citation.

This RFC defines a **PDF-specific** pipeline that produces a normalized intermediate representation, then distills into the canonical `ParsedDocument` contract defined in [`../parsers/01_rfc.md`](../parsers/01_rfc.md).

---

## 2. Scope

### 2.1 In scope (this RFC)
- **Stage A:** Run **Marker and MinerU in parallel** as primary extractors.
- Page-level candidate scoring, selection, and deterministic fallbacks to a placeholder block.
- A normative **intermediate schema** for PDF extraction output.
- A normative **distillation algorithm**: intermediate → `ParsedDocument` (per [`../parsers/01_rfc.md`](../parsers/01_rfc.md)).

### 2.2 Out of scope (this iteration)
- Strict eval harness / KPIs / metrics gates as acceptance criteria.
- Learned routing (ML classifier) beyond deterministic heuristics.
- “Table as data” extraction (e.g., Camelot) as a required component (allowed as future extension).
- Perfect WYSIWYG reproduction.

---

## 3. Relationship to [`../parsers/01_rfc.md`](../parsers/01_rfc.md) (authoritative contract)

[`../parsers/01_rfc.md`](../parsers/01_rfc.md) is the **single authoritative contract** for `RawDocument → ParsedDocument` invariants and anchors.

This RFC adds a **PDF-specific pre-distillation pipeline**:

```
RawDocument (PDF bytes)
   └─ Hybrid PDF Pipeline  →  ExtractedPdfDocument (intermediate, PDF-specific)
                               └─ Distiller  → ParsedDocument (per [`../parsers/01_rfc.md`](../parsers/01_rfc.md))
```

### 3.1 Contract summary (non-exhaustive)
- Input: `RawDocument` with `content_type=application/pdf` (see [`../parsers/01_rfc.md`](../parsers/01_rfc.md) for the canonical `RawDocument` schema).
- Output (canonical): `ParsedDocument` per [`../parsers/01_rfc.md`](../parsers/01_rfc.md) (this RFC MUST NOT change that schema).
- Output (pipeline artifacts): `ExtractedPdfDocument` (this RFC’s intermediate schema, §9) plus selection logs/artifacts (§12).

---

## 4. Goals and non-goals

### 4.1 Goals
- **Coverage:** every page produces at least one text-bearing block (best effort; see §13 for failure policy).
- **Structural fidelity:** preserve headings/lists/tables/code where present.
- **Determinism:** same inputs + versions + configs yield identical `ParsedDocument` and stable intermediate output.
- **Traceability:** every emitted block can be traced to `{page_idx, bbox/poly, engine, engine_artifact_ref}`.

### 4.2 Non-goals
- Pixel-perfect layout reproduction.
- Perfect equation semantics.
- Guaranteed “cells” for all tables.

---

## 5. Terminology

- **Engine:** a PDF extraction backend (Marker, MinerU).
- **Candidate:** a per-page extraction result produced by an engine before selection.
- **Block:** an atomic content unit (paragraph/list/table/code/caption/etc.).
- **Asset:** non-text payload (image crop, figure, equation image, table render).
- **Intermediate document:** `ExtractedPdfDocument` (PDF-specific normalized form).
- **Distillation:** deterministic transformation from intermediate → `ParsedDocument`.

---

## 6. High-level pipeline

### 6.1 Stages (normative)
A. **Primary extraction (parallel):** run Marker + MinerU for the full document.  
B. **Candidate selection:** per-page scoring + selection.  
C. **Normalize & merge:** merge selected candidates into `ExtractedPdfDocument`.  
D. **Distill:** produce `ParsedDocument` per [`../parsers/01_rfc.md`](../parsers/01_rfc.md).

### 6.2 Determinism policy (normative)
The pipeline MUST be deterministic given:
- identical `content_bytes`,
- identical pipeline version,
- identical engine versions,
- identical config (including timeouts).

If an engine is inherently non-deterministic, the implementation MUST:
- pin versions and seeds where supported, and
- record `engine_config_hash` and `engine_version` in artifacts and intermediate metadata.

---

## 7. Stage A — Primary extraction (Marker + MinerU parallel)

### 7.1 Execution unit
- Engines SHOULD be run in a page-batched mode if supported, but results MUST be representable at **page granularity**.
- Timeouts MUST be specified per engine:
  - `marker_timeout_s`
  - `mineru_timeout_s`

### 7.2 Stage A outputs (required)
For each engine run:
- `engine_artifact_ref`: stable identifier to all artifacts produced for the run (directory path, object-store key, or content hash).
- `engine_pages[]`: a per-page candidate object including:
  - extracted text (if available),
  - structural hints (if available),
  - block list with coordinates (if available),
  - extracted assets references (if available),
  - parse status (ok/timeout/error/empty).

Stage A MUST NOT discard “losing” outputs; selection happens later.

---

## 8. Stage B — Candidate selection (page-level)

### 8.1 Candidate normalization (pre-selection)
Before scoring, each engine’s output MUST be adapted into a shared **candidate model**:

`PageCandidate` (conceptual):
- `page_idx`
- `blocks[]` (each with `type`, `text`, optional `bbox/poly`)
- `assets[]` (optional)
- `signals` (computed heuristics, see below)
- `status`: `ok|empty|error|timeout`

### 8.2 Signals (deterministic heuristics)
For each candidate, compute:
- `char_count`: count of non-whitespace characters in all text blocks.
- `block_count`
- `line_count` (after canonical line splitting)
- `duplicate_line_ratio`: duplicates / total lines (normalized lines).
- `heading_like_count` (optional heuristic: lines starting with `#` or matching heading patterns).
- `has_coords`: whether most blocks have bbox/poly.
- `asset_count`

### 8.3 Scoring + selection algorithm (normative)
For each page:
1) If exactly one candidate has `status=ok`, select it.
2) If both are ok, compute a deterministic score:

Example scoring function (normative structure; weights are config):
- `score = w_chars * log1p(char_count)`
- `+ w_blocks * log1p(block_count)`
- `- w_dupes * duplicate_line_ratio`
- `+ w_coords * I(has_coords)`
- `+ w_headings * log1p(heading_like_count)`
- `+ w_assets * log1p(asset_count)`

Select the candidate with higher score. Ties break deterministically:
1) prefer Marker, then
2) prefer MinerU.

3) If both candidates are `empty|error|timeout`, mark page as **failed** (will emit a placeholder block in Stage C).

### 8.4 Outputs from Stage B (required)
- `selected_engine_by_page[page_idx]`
- `selection_reason_by_page[page_idx]` (compact enum + key signals)

---

## 9. Stage C — Intermediate schema: `ExtractedPdfDocument` (normative)

### 9.1 Top-level schema
```json
{
  "doc_id": "string",
  "source_pdf": {
    "content_hash": "string",
    "page_count": 0,
    "metadata": { "title": "string", "...": "..." }
  },
  "pipeline": {
    "pipeline_version": "string",
    "config_hash": "string"
  },
  "engine_runs": [
    {
      "engine": "marker|mineru",
      "engine_version": "string",
      "engine_config_hash": "string",
      "engine_artifact_ref": "string",
      "status": "ok|partial|error"
    }
  ],
  "pages": [
    {
      "page_idx": 0,
      "width": 0,
      "height": 0,
      "selected_engine": "marker|mineru",
      "selection_reason": "string",
      "blocks": [],
      "assets": [],
      "diagnostics": { "...": "..." }
    }
  ]
}
```

### 9.2 Block schema (required)
```json
{
  "block_id": "string",
  "type": "heading|para|list|table|code|caption|footer|header|unknown",
  "text": "string",
  "page_idx": 0,
  "bbox": [0, 0, 0, 0],
  "poly": [[0,0],[0,0],[0,0],[0,0]],
  "reading_order_key": "string",
  "source": {
    "engine": "marker|mineru",
    "engine_artifact_ref": "string",
    "engine_block_ref": "string"
  },
  "confidence": 1.0,
  "metadata": { "...": "..." }
}
```

Rules:
- Exactly one of `bbox` or `poly` MUST be present if coordinates are available; both MAY be present.
- `reading_order_key` MUST be stable and comparable as a string, inheriting the native block order from the selected engine.
- `source.engine_artifact_ref` MUST be present for reproducible debugging.

### 9.3 Asset schema (optional but recommended)
```json
{
  "asset_id": "string",
  "type": "image|figure|equation|table_render",
  "page_idx": 0,
  "path_or_ref": "string",
  "bbox_or_poly": "...",
  "source": { "engine": "marker|mineru", "engine_artifact_ref": "string" },
  "metadata": { "mime": "image/png", "...": "..." }
}
```

---

## 10. Stage D — Distillation algorithm (intermediate → `ParsedDocument`) (normative)

The distiller converts `ExtractedPdfDocument` into the canonical `ParsedDocument` schema and invariants defined in [`../parsers/01_rfc.md`](../parsers/01_rfc.md).

### 10.1 Output constraints (from [`../parsers/01_rfc.md`](../parsers/01_rfc.md))
- Emit `canonical_text` (UTF-8).
- Emit `structure_tree` with block leaf nodes, each containing valid `range` into `canonical_text`.
- Emit deterministic anchors: `doc_anchor`, `sec_anchor`, `pass_anchor`.
- Ensure determinism and hierarchical integrity.

### 10.2 Deterministic ordering (reading order)
For each page, blocks are sorted by `reading_order_key`, which MUST represent the native block order returned by the selected engine.

### 10.3 Canonical text construction
- Iterate pages in ascending `page_idx`.
- Within each page, iterate blocks in reading order.
- Append each block’s serialized text to `canonical_text` with deterministic separators:
  - Between blocks: `\n\n`
  - Between pages: `\n\n\f\n\n` (form feed delimiter), configurable but MUST be deterministic and versioned.

### 10.4 Structure reconstruction
The distiller MUST produce a `structure_tree` that is stable and minimally useful.

Baseline rules (normative, deterministic):
- Create a root `doc` node.
- Convert `heading` blocks into heading nodes with levels:
  - If the block includes an explicit level (from Marker `#`), use it.
  - Else infer a level using deterministic heuristics (font-size not available → fallback to level 1).
- Non-heading blocks become leaves under the most recent heading, or under root if no heading has been seen.
- `code` blocks MUST preserve verbatim text (except newline normalization).
- `table` blocks MAY serialize as:
  - Markdown table if available; else
  - fenced block with a `table:` prefix and best-effort text.

### 10.5 Range computation
For each leaf block, compute `[start, end)` offsets into `canonical_text`:
- `start` is the offset where the block serialization begins.
- `end` is the offset after the last character of the block serialization (excluding inter-block separators).

### 10.6 Anchor derivation
Follow [`../parsers/01_rfc.md`](../parsers/01_rfc.md):
- `doc_anchor = hash(doc_id)`
- `sec_anchor = hash(doc_id + normalized_section_path)`
- `pass_anchor = hash(sec_anchor + block_type + block_ordinal_within_section)`

The distiller MUST:
- normalize `section_path` deterministically (casefold + trim + canonical whitespace),
- apply ordinal suffixes for duplicate sibling headings,
- record the hash algorithm/version in `ParsedDocument.metadata.parser_version` and/or a dedicated field.

### 10.7 Provenance preservation
`ParsedDocument.metadata` SHOULD include:
- `pdf_pipeline_version`
- `selected_engine_counts` (counts per engine)
- `engine_runs[]` summary
- a pointer to the intermediate artifact (`intermediate_artifact_ref`) when available

---

## 11. Configuration surface (normative)

Example config (TOML-like):
```toml
[pdf_hybrid]
marker_timeout_s = 120
mineru_timeout_s = 180

[selection_weights]
w_chars = 1.0
w_blocks = 0.2
w_dupes = 2.0
w_coords = 0.3
w_headings = 0.2
w_assets = 0.1
```

All config values that affect output MUST be included in `config_hash`.

---

## 12. Logging and artifacts (pipeline-only)

This RFC does not require a full evaluation harness, but it does require **reproducible artifacts**.

Required outputs (per document parse):
- `engine_artifacts/marker/...`
- `engine_artifacts/mineru/...`
- `selection_log.jsonl` (one record per page: scores, chosen engine, reasons)
- `extracted_pdf_document.json` (the intermediate schema)
- `parsed_document.json` (final `ParsedDocument`)

---

## 13. Failure policy

- The pipeline SHOULD be best-effort: partial page failures must not fail the entire document unless configured.
- If a page cannot be extracted by any engine, the pipeline MUST still emit:
  - an empty placeholder block with `type=unknown` and diagnostic info in the intermediate,
  - and a corresponding minimal placeholder text in `canonical_text` (e.g., `[UNPARSEABLE PAGE N]`) so downstream systems remain stable.
- Such placeholders MUST be deterministic and versioned.

---

## 14. Rollout plan
- Feature-flag the hybrid pipeline by source/type:
  - `enable_hybrid_pdf_pipeline = true` for PDFs only.
- Start with “shadow mode” (produce intermediate + parsed output for comparison, not used for indexing).
- Gradually enable as primary for selected corpora.

---

## 15. Open questions / future work
- Optional “table as data” sidecar (Camelot) behind a config flag.
- Better heading-level inference using engine-specific style cues.
- Formal metrics + regression harness (deferred by this iteration).
