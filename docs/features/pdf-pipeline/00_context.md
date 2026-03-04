# Context: Hybrid PDF Pipeline Wiring (run_pdf_pipeline)

**Status:** Draft
**Last updated:** 2026-03-04

## Purpose
Implement the production-path wiring for the Hybrid PDF pipeline by completing
`src/docforge/parsers/pdf_hybrid/pipeline.py::run_pdf_pipeline()` so that PDFs
are parsed via Marker + MinerU (parallel), assembled into the RFC intermediate
schema, and distilled into canonical `ParsedDocument` outputs behind an existing
feature flag.

This is a separate feature from the E2E harness in `docs/features/e2e/`:
- E2E harness: developer tooling to run on local corpora and validate end-to-end.
- Pipeline wiring: production parsing path implementation (even if feature-flagged).

## Contract sources of truth
- Hybrid pipeline semantics and intermediate schema:
  - `docs/features/hybrid-parsers/01_rfc.md`
- Canonical parser contract (ParsedDocument invariants, anchors, ranges):
  - `docs/features/parsers/01_rfc.md`

## Current state
- `src/docforge/parsers/pdf_hybrid/pipeline.py::run_pdf_pipeline()` is stubbed and raises
  `NotImplementedError`.
- `src/docforge/parsers/default.py` attempts to call `run_pdf_pipeline()` when
  `enable_hybrid_pdf_pipeline=True`, but only catches `NotImplementedError` and then
  falls back to legacy canonicalization.

## Primary risks
- Stream-drain bug: PDF bytes can only be drained once (`content_stream`), so pipeline
  failure can cause empty fallback.
- Engine isolation: Marker/MinerU heavy deps must not pollute the root env.
- Determinism: identical bytes/config/engine versions must yield identical intermediate + parsed
  artifacts.
- Artifact stability: outputs must be reproducible for debugging and diffing.

