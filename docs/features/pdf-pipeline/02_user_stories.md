# User Stories: Hybrid PDF Pipeline Wiring

**Status:** Draft
**Last updated:** 2026-03-04

## Primary stories
- As a developer, when `enable_hybrid_pdf_pipeline=True` and a PDF is parsed, the parser runs Marker
  and MinerU (if available), selects per-page candidates deterministically, and returns a valid `ParsedDocument`.
- As a developer, I can disable artifacts without changing parsing behavior.
- As a developer, I can force a single engine via config for emergency mitigation.

## Acceptance checks
- `run_pdf_pipeline()` returns an `ExtractedPdfDocument` that validates and matches
  `docs/features/hybrid-parsers/01_rfc.md` Section 9.
- `distill_pdf(extracted_doc, config)` returns a `ParsedDocument` that passes strict invariants in
  `src/docforge/parsers/models.py`.
- Artifact emission (when enabled) produces stable, reproducible outputs with complete provenance:
  - `engine_artifact_ref` present in intermediate and per-block `source.engine_artifact_ref`.
- Running the pipeline twice with identical PDF bytes, engine versions, and config produces byte-identical artifacts.

## Failure mode stories
- One engine missing:
  - Pipeline continues with the available engine and records engine_runs status for the missing engine appropriately.
- Both engines missing:
  - Pipeline raises a pipeline-unavailable error and the parser falls back (no placeholder indexing of fake content by default).
- Engine timeout:
  - Timeout is recorded; selection continues with remaining candidates or placeholder policy.
- Both engines fail on a page:
  - Page becomes a deterministic placeholder block and placeholder text in distillation.

## Rollback/mitigation
- Feature flag: `enable_hybrid_pdf_pipeline` remains default False.
- `pdf_hybrid.force_engine` supports emergency routing.
- `pdf_hybrid.emit_artifacts` supports storage/IO mitigation.

