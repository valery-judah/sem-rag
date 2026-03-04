# Context: E2E Evaluation Harness (Hybrid PDF)

**Status:** Draft
**Last updated:** 2026-03-04

## Purpose
We need a local, end-to-end evaluation harness that runs the Hybrid PDF pipeline
components against real PDFs in `data/` (gitignored), validates adapter and
distillation contracts, and emits reproducible debug artifacts.

This harness is a developer workflow to reduce regressions and integration drift
for:
- Marker and MinerU engine integration
- Adapter normalization
- Deterministic selection
- Intermediate artifact emission
- Distillation into canonical `ParsedDocument`

## Related feature contracts
- Hybrid PDF pipeline contract and required artifacts live in:
  - `docs/features/hybrid-parsers/01_rfc.md`
- Canonical parser output contract lives in:
  - `docs/features/parsers/01_rfc.md`

## Non-goals
- Running real engines in CI.
- Defining quality metrics gates (beyond contract and determinism).
- Implementing the Hybrid PDF pipeline itself (e.g. `run_pdf_pipeline()` wiring).

