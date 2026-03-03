# Design: Hybrid PDF Parsing Pipeline

## 1. Design Goals
- Implement a deterministic PDF pipeline satisfying [`./01_rfc.md`](./01_rfc.md) while preserving the canonical `ParsedDocument` contract in [`../parsers/01_rfc.md`](../parsers/01_rfc.md).
- Maximize best-effort page coverage without failing entire documents for partial extraction failures.
- Preserve traceability from final blocks back to page geometry and engine artifacts.
- Keep selection and ordering stable and explainable (no learned routing in this iteration).

## 2. Data Flow
1. Receive `RawDocument` (PDF bytes) from connectors.
2. Run Marker and MinerU extraction (parallel; persisted artifacts per engine).
3. Adapt engine outputs into normalized `PageCandidate` objects.
4. Compute deterministic signals and score candidates per page.
5. Merge selected blocks/assets into `ExtractedPdfDocument` with provenance and native engine `reading_order_key`.
6. Distill `ExtractedPdfDocument` into canonical `ParsedDocument` (stable text + structure + anchors).

## 3. Algorithms and Tie-Breakers

### 3.1 Candidate normalization
- Convert each engine’s per-page output into a shared candidate model:
  - `blocks[]` with `{type, text, bbox/poly?}`
  - `status` (`ok|empty|error|timeout`)
  - `assets[]` references (optional)
- Do not discard non-selected candidates; persist them as engine artifacts for debugging.

### 3.2 Signals and scoring
- Compute deterministic signals (`char_count`, `block_count`, `duplicate_line_ratio`, `has_coords`, `asset_count`).
- Score using a weight-configured function (see [`01_rfc.md §8.3`](./01_rfc.md)) and break ties deterministically:
  - prefer Marker, then MinerU.

### 3.3 Config hashing and versioning
- All output-affecting config values are included in `config_hash`.
- Each engine run records `engine_version` and `engine_config_hash` in `engine_runs[]` for reproducibility.

## 4. Edge-Case Handling
- Full-engine failure on a page: score the remaining successful candidate.
- Page remains empty after both engines fail: emit a deterministic placeholder block and placeholder text during distillation.

## 5. Tradeoff Decisions
- Removal of OCR and PyMuPDF fallbacks:
  - Pros: significantly reduced complexity, lower latency, fewer dependencies, simpler determinism guarantees.
  - Cons: pages that Marker/MinerU both struggle with will simply be replaced by a placeholder rather than recovered via OCR.
- Intermediate schema + artifact logging:
  - Pros: reproducible debugging and explainable selection decisions.
  - Cons: increased storage footprint.
- Deterministic heuristics over learned routing:
  - Pros: predictable behavior and easier contract testing.
  - Cons: may miss nuanced routing opportunities for complex layouts.

## 6. Observability
- Events:
  - `PdfHybridEngineRunCompleted(doc_id, engine, status, duration_ms)`
  - `PdfHybridPageSelected(doc_id, page_idx, selected_engine, signals, score, reason)`
  - `PdfHybridPlaceholderEmitted(doc_id, page_idx, reason)`
- Payload fields:
  - `doc_id`, `page_idx`, `engine`, `engine_version`, `config_hash`
  - `char_count`, `block_count`, `duplicate_line_ratio`, `has_coords`
  - `selected_engine`, `selection_reason`

## 7. Performance and Complexity Notes
- Parallel extraction is the primary throughput win; keep scoring and merging linear in block counts.
- With OCR and PyMuPDF removed, CPU overhead per page is bounded entirely by Marker and MinerU logic.

## 8. Limitations and Deferred Items
- No ML classifier for routing/quality estimation in this iteration.
- No requirement for “table as data” extraction; tables remain best-effort structural blocks.

