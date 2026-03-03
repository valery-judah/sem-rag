# Context: Hybrid PDF Parsing Pipeline

## Purpose in Pipeline
- Component: PDF-specific extraction + normalization + distillation (prepares `ParsedDocument` for downstream chunking).
- Module path: `src/docforge/parsers/` (proposed subpackage: `src/docforge/parsers/pdf_hybrid/`).
- Upstream dependency: Source connectors emit `RawDocument` with `content_type=application/pdf`.
- Downstream dependency: Chunking/segmenter consumes `ParsedDocument` from [`../parsers/01_rfc.md`](../parsers/01_rfc.md).

## Component Boundaries
### Owns
- Running Marker + MinerU extraction in parallel for all PDF pages.
- Deterministic per-page candidate scoring/selection and tie-breaks.
- Emission of a normalized intermediate artifact (`ExtractedPdfDocument`) with per-block provenance.
- Distillation into canonical `ParsedDocument` (without changing the `ParsedDocument` contract itself).

### Does Not Own
- Connector fetch/sync behavior, source enumeration, or ACL normalization.
- Non-PDF parsing behavior (HTML/Markdown/plain text).
- Downstream chunk sizing/overlap and retrieval/ranking policies.
- Learned routing (ML classifiers) beyond deterministic heuristics.

## Contract References
- Normative contracts: [`./01_rfc.md`](./01_rfc.md), [`../parsers/01_rfc.md`](../parsers/01_rfc.md)

## Invariants Summary
- Determinism: identical bytes + engine versions + config => identical intermediate + `ParsedDocument`.
- Coverage best-effort: each page yields at least one text-bearing block (or a deterministic placeholder).
- Traceability: every emitted block is attributable to `{page_idx, bbox/poly, engine, engine_artifact_ref}`.
- Stable ordering: blocks inherit the native order from the selected engine and have stable page delimiters.

## Golden Example (Compact)
Input:
```text
PDF with 2 pages:
- Page 0: digital-born text (2-column).
- Page 1: scanned image with printed text.
```

Expected outcomes:
- Page 0 selects Marker or MinerU deterministically via scoring; blocks have stable reading order from the engine and coordinates when available.
- Page 1 selects Marker or MinerU deterministically via scoring (or emits a placeholder if both engines fail).
- `ExtractedPdfDocument` records `selected_engine`, `selection_reason`, and per-block provenance for both pages.
- Distilled `ParsedDocument.canonical_text` includes deterministic block separators and a deterministic page delimiter.

## Verification Map
| Contract area | Verification family | Example checks |
|---|---|---|
| Determinism | Snapshot/property | Re-run yields byte-identical `extracted_pdf_document.json` and `ParsedDocument` |
| Coverage | Corpus/fixture | Scan-heavy fixtures produce non-empty page outputs (or placeholders) |
| Traceability | Unit/property | Every block has `{page_idx, source.engine, source.engine_artifact_ref}` |
| Ordering | Unit/fixture | Multi-column fixtures preserve stable block reading order |
