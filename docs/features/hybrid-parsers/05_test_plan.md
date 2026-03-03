# Test Plan: Hybrid PDF Parsing Pipeline

## Scope
- Validate deterministic candidate selection from Marker and MinerU engines.
- Ensure best-effort page coverage with placeholder blocks on extraction failure.
- Verify intermediate schema emission (`extracted_pdf_document.json`) and provenance traceability.
- Verify deterministic distillation into `ParsedDocument` canonical format with stable page delimiters.

## Test Pyramid
- Unit: 
  - Adapter normalization logic per engine.
  - Deterministic scoring, signals calculation, and tie-breaking algorithms.
  - Placeholder block creation and fallback logic.
  - Intermediate schema to `ParsedDocument` distillation algorithm.
- Property: 
  - Traceability completeness (all blocks contain required `source.engine` and `engine_artifact_ref`).
  - Score stability across equivalent inputs.
- Snapshot: 
  - Intermediate schemas (`extracted_pdf_document.json`) and `ParsedDocument` outputs on a fixed set of PDF fixtures to guarantee exact determinism.
  - `selection_log.jsonl` stability.
- Integration: 
  - End-to-end pipeline run (Connector -> RawDocument -> Hybrid Pipeline -> ParsedDocument) over real-world PDF layouts.

## Fixtures and Corpora
- Mixed digital-born and scan-heavy layout PDFs.
- Multi-column PDFs requiring reading-order reconstruction.
- Malformed PDFs to test fallback/timeout handlers.
- Empty PDFs or entirely image-based PDFs without embedded text.

## CI Gates
- Determinism check: `make test` repeatedly runs snapshot comparisons and must produce identical byte-for-byte outcomes.
- Test coverage on parsing algorithms (scoring, merging, distillation) > 90%.
- Provenance validation gates: zero blocks missing required metadata.

## Snapshot Update Policy
- Snapshot updates require explicit PR review confirming the structural change is intentional and improves correctness without violating [`../parsers/01_rfc.md`](../parsers/01_rfc.md) contracts.
- Changes to engine versions or score weights mandate a snapshot update.

## Reporting
- Test execution reports via `pytest` (invoked via `make test`).
- Logging for page extraction outcomes (OK, Placeholder, Error).
