# Hybrid PDF Parsers — Routing Strategies & Patterns (RFC Notes)

Context: Marker is usually best overall, but for at least one document with citations + notes in separate blocks, MinerU produced clearly better structure; this doc extracts routing patterns to reuse in the hybrid-parsers RFC. [file:73]

---

## Goals and non-goals

### Goals
- Maximize non-empty content rate and structural fidelity on technical textbooks (figures, equations, tables) while keeping cost/latency predictable. [file:73]
- Make downstream chunking independent of the upstream parser by enforcing a normalized output contract. [file:73]
- Exploit complementary failure modes via explicit fallback logic (catastrophic “no output” vs partial empty pages vs reading-order glitches). [file:73]

### Non-goals
- Perfect WYSIWYG reproduction; the aim is stable, segmentable text + assets with traceability to page regions. [page:4][page:3]

---

## Library roles (capability summary)

- Marker: converts PDFs to Markdown + JSON and can also output HTML/chunks; supports image extraction and formatting features that make it a strong default for technical PDFs. [page:4]
- MinerU: produces Markdown plus structured artifacts (notably `content_list.json`) that are convenient for block-level segmentation with page index + bboxes, which helps on layout-heavy pages (e.g., citations/notes). [page:3]
- PyMuPDF (fitz): fast geometry-first extractor; can return words/blocks with coordinates, enabling cheap page classification and custom reading-order reconstruction. [web:17][web:18]
- Camelot (optional sidecar): table specialist; lattice leverages ruling lines and stream uses text layout heuristics—use it only when you need “table as data,” not just “table as readable.” [web:34]

---

## Routing strategies / patterns

### Pattern A — “Default + Exception Pages” (recommended)
**Idea**: Run a cheap PyMuPDF pre-pass to classify each page, then parse the document with a default engine (Marker), and re-parse only exception pages with MinerU (or specialists). [web:17][web:18][file:73]

Why it works:
- Marker gives a good Markdown baseline with minimal output-format configuration overhead. [page:4]
- MinerU is reserved for the subset of pages where layout complexity (citations/notes blocks, dense figures) is worth the GPU cost, and its block list + bbox artifacts reduce downstream heuristics. [page:3]
- PyMuPDF keeps routing cheap and explainable via geometry-derived features. [web:17][web:18]

When to choose:
- Mostly digital-born PDFs with occasional “hard” pages. [file:73]

### Pattern B — “Per-page tournament” (robust but heavier)
**Idea**: For each page, run a competition: try Marker; if quality gates fail, try MinerU; if that fails, fall back to PyMuPDF. [file:73]

Why it works:
- You turn parser brittleness into deterministic fallbacks aligned with your “every page parsed” success criteria. [file:73]

When to choose:
- High-stakes corpora where missing content is unacceptable and you can afford more GPU work. [file:73]

### Pattern C — “Table extraction sidecar”
**Idea**: Keep the main parser focused on readable structure, but when a page is table-heavy and you need structured cells, run Camelot and store the result alongside the baseline render. [web:34][page:3]

Why it works:
- Layout parsers preserve tables visually (often as HTML or imperfect Markdown), while table specialists can yield a cell grid when the PDF encoding supports it. [web:34][page:3]

---

## Page feature extraction (PyMuPDF pre-pass)

Use PyMuPDF to compute per-page features from words/blocks because it is fast and provides the geometry primitives needed for routing. [web:17][web:18]

Minimum features:
- Embedded text density: char/word count, block count, average block area/width/height. [web:18]
- Raster dominance: low text density + high image presence (or “text missing” signals) to trigger OCR/hi-res paths. [file:73]
- Table-likeness: many aligned short text runs into grid-like rows/columns; optionally detect ruling lines (which correlates with Camelot lattice success). [file:73][web:34]

Additions for “citations + notes in separate blocks”:
- Margin-notes likelihood: many small blocks clustered near left/right margins (outer ~15–20% of width), optionally smaller font spans if you use dict/span metadata. [web:18]
- Multi-column likelihood: block centers cluster into 2+ x-axis bands; do not trust naïve “sort by y then x” ordering for these pages. [web:21][web:74]
- Footnote density: many short lines near the bottom band of the page (often correlates with citation-heavy layouts). [file:73]

---

## Routing decision matrix (rules of thumb)

- Single-column, text-heavy, low exception signals → PyMuPDF extraction is often sufficient (fast, deterministic), but only if you keep column-aware ordering as a guardrail. [web:17][web:21]
- Rich structure needed (headings, references, mixed formatting) → Marker as default. [page:4]
- Citations/notes as separate blocks (high margin-notes likelihood) or dense figure-heavy layouts → MinerU for that page subset; consume `content_list.json`-like block lists for segmentation. [page:3]
- Table candidate and you need structured data → Camelot sidecar; keep Marker/MinerU’s rendering as fallback so you never drop content. [web:34][page:4][page:3]

---

## Fallback policy (explicit + logged)

Observed failure modes differ (MinerU “no parseable output” vs Marker empty pages), so define a strict chain with timeouts and quality gates. [file:73]

Recommended chain (page-level):
1) Marker (primary): strongest low-config Markdown baseline. [page:4]
2) MinerU (secondary): apply on routed “hard layout” pages or when Marker fails gates. [page:3][file:73]
3) PyMuPDF (tertiary safety net): always return something (even if structure is simpler). [web:17][web:18]

Quality gates (examples):
- Near-empty output on a page where PyMuPDF indicates substantial embedded text. [web:18][file:73]
- Duplicate-line spikes or obvious order scrambling (use the metrics you already produce). [file:73]

---

## Normalized output contract (downstream should consume this)

Downstream chunking should only depend on a single normalized model (`ParsedDocument`) so routing/engines remain swappable. [file:73]

Suggested minimum schema:
- Document metadata: `source_pdf`, `pipeline_version`. [file:73]
- `pages[]`: `{page_idx, width, height}`. [page:3]
- `blocks[]`: `{page_idx, block_id, type, text, bbox, reading_order_key, engine, engine_artifact_ref}`; PyMuPDF supports bbox extraction for blocks/words and MinerU provides bbox-linked block lists. [web:18][page:3]
- `assets[]`: `{page_idx, asset_id, type=image|figure_crop, path, bbox, engine}`; both Marker and MinerU workflows emphasize image extraction. [page:4][page:3]
- `tables[]` (optional): allow `{markdown, html, cells}` simultaneously because complex tables may be better preserved as HTML while “table as data” needs cells when available. [page:3][page:4][web:34]

Operational note:
- Store `engine_artifact_ref` (path/hash) for reproducible debugging without re-running GPU parses. [file:73]

---

## Implementation notes (practical)

- Prefer two-pass execution: (1) PyMuPDF classification for all pages, (2) schedule heavy parses only for pages that need them. [web:17][web:18]
- Make routing explainable: persist router decisions + features + thresholds (e.g., `router_decisions.jsonl`) to tune policies iteratively. [file:73]
- Avoid merging by concatenating Markdown strings; merge by normalized block lists to prevent ordering artifacts. [file:73][page:3]

---

## Evaluation signals (what to measure)

Keep these as first-class KPIs for routing changes:
- Coverage: non-empty content rate overall and by page type (text-heavy vs table-heavy vs margin-notes). [file:73]
- Failure taxonomy: timeout, “no parseable output,” empty page, severe order issues. [file:73]
- Stability: output variance for the same doc across runs/versions (catch nondeterminism). [file:73]
- Chunk quality proxies: duplicate line rate, heading continuity, orphan captions, table integrity on a labeled subset. [file:73]

---

## Suggested default policy (ready to implement)

1) Pre-pass (PyMuPDF): compute features per page (text density, multi-column likelihood, margin-notes likelihood, table-likeness). [web:17][web:18][web:21]
2) Primary parse: Marker for all pages except those flagged as “hard layout.” [page:4]
3) Exception parse: MinerU for flagged pages; merge results at the normalized block level. [page:3][file:73]
4) Tables sidecar: Camelot on table-like pages only when you need structured data; store both the visual table (Marker/MinerU) and the cell grid (Camelot) when available. [web:34][page:3]
5) Safety net: if any page fails gates, re-run with next fallback; always emit a ParsedDocument with at least one block per page. [web:17][file:73]
