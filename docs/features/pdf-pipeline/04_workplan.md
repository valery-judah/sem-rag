# Workplan: Hybrid PDF Pipeline Wiring

**Status:** Draft
**Last updated:** 2026-03-04

## Summary
Implement `run_pdf_pipeline()` and required wiring so that PDFs can be parsed via hybrid engines
behind a feature flag, with deterministic intermediate artifacts and stable distillation outputs.

## PR Plan (phased, with exit criteria)

### PR1: Feature docs (this directory)
Scope:
- Add `docs/features/pdf-pipeline/` feature artifact set.
- Cross-link to:
  - `docs/features/hybrid-parsers/01_rfc.md`
  - `docs/features/parsers/01_rfc.md`
  - `docs/features/e2e/*`

Exit criteria:
- Docs are internally consistent and reference real code paths.

Checks:
- Docs-only.

### PR2: Safe byte materialization + config plumbing
Scope:
- Modify `src/docforge/parsers/default.py` to materialize PDF bytes once and rewrap `RawDocument`
  for pipeline.
- Extend `ParserConfig` to include `pdf_hybrid: PdfHybridConfig`.
- Add `pypdf` dependency.

Exit criteria:
- PDF pipeline failures no longer cause empty fallback due to drained streams.
- Tests updated accordingly.

Checks:
- `make fmt`, `make lint`, `make type`, `make test`.

### PR3: Engine runner layer (subprocess, tools isolation)
Scope:
- Add internal runner modules and manifest structure.
- Implement engine discovery under `tools/` isolation.
- Implement version detection and timeout handling.

Exit criteria:
- Runner code is unit-tested without requiring engines.
- Local manual run works when tools are provisioned.

Checks:
- `make fmt`, `make lint`, `make type`, `make test`.

### PR4: Implement run_pdf_pipeline() with injected runners + CI-safe tests
Scope:
- Implement assembly logic using injection to avoid real engine dependency in tests.
- Add determinism/snapshot tests using fake raw outputs.
- Implement artifact emission behavior (default ON, configurable OFF).

Exit criteria:
- CI tests pass without engines.
- Outputs validate (`ExtractedPdfDocument`, `ParsedDocument`).

Checks:
- `make fmt`, `make lint`, `make type`, `make test`.

### PR5: Local-only real engine smoke path (not in CI)
Scope:
- Wire default `run_pdf_pipeline()` to real subprocess runners.
- Add documented local smoke workflow and troubleshooting notes.

Exit criteria:
- On a machine with tool envs provisioned and models available, hybrid parsing produces artifacts and
  parsed output.

Checks:
- `make test` (CI), manual local smoke step documented.

## Definition of Done
- `run_pdf_pipeline()` fully implemented and deterministic.
- Parsing PDFs with feature flag yields valid `ParsedDocument`.
- Artifacts are reproducible and provenance-complete when enabled.
- No unrelated files modified.

