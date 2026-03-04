# User Stories: E2E Evaluation Harness (Hybrid PDF)

**Status:** Draft
**Last updated:** 2026-03-04

## Primary stories
- As a developer, I can run `make e2e-pdf` to execute Marker and MinerU (if installed)
  on all PDFs under `data/` and get a per-document artifact bundle suitable for debugging.
- As a developer, I can run the harness on a subset (`--limit`, include/exclude) to iterate quickly.
- As a developer, I can run with only one engine available and still get intermediate + parsed
  outputs with deterministic placeholder behavior.

## Acceptance checks
- For each PDF processed, the harness writes:
  - `selection_log.jsonl`
  - `extracted_pdf_document.json`
  - `parsed_document.json`
  - `summary.json`
- `parsed_document.json` MUST validate as `ParsedDocument` (strict invariants, ranges in bounds).
- Intermediate `engine_artifact_ref` and block provenance `source.engine_artifact_ref` MUST match
  the artifact directory structure.
- Running the harness twice with identical inputs, tool locks, and config MUST produce byte-identical
  JSON outputs for:
  - `selection_log.jsonl`
  - `extracted_pdf_document.json`
  - `parsed_document.json`
  - `summary.json`

## Failure mode stories
- Missing `data/`:
  - Harness exits non-zero with a message explaining `data/` is local/gitignored and how to provide
    `--data-dir`.
- Engine timeout:
  - Harness records timeout in `engine_runs` and emits deterministic placeholder blocks for impacted pages.
- Engine output drift:
  - Harness fails with a clear error pointing to the failing adapter stage and the `engine_artifact_ref`
    directory.

