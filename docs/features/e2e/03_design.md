# Design: E2E Evaluation Harness (Hybrid PDF)

**Status:** Draft
**Last updated:** 2026-03-04

## 1. Entry points
- `make tools-sync` provisions tool envs:
  - `uv sync --project tools/marker`
  - `uv sync --project tools/mineru`
- `make e2e-pdf` runs:
  - `uv run python scripts/e2e_hybrid_pdf_eval.py --data-dir data`

## 2. Modules and responsibilities
- `scripts/e2e_hybrid_pdf_eval.py`
  - Discover PDFs, derive `doc_id` and `run_hash`
  - Execute engines through runner modules
  - Load raw JSON outputs, run adapters
  - Run selection, assemble `ExtractedPdfDocument`
  - Emit artifacts and distill to `ParsedDocument`
  - Write `summary.json`

- `src/docforge/parsers/pdf_hybrid/engines/run_manifest.py`
  - Pydantic `EngineRunManifest` for reproducible bookkeeping
  - Captures command, env overrides, timings, return codes, primary output paths

- `src/docforge/parsers/pdf_hybrid/engines/marker_cli.py`
  - Resolve Marker binary from `tools/marker/.venv/bin/marker_single` then fallback
  - Execute Marker, write logs, write manifest
  - Determine canonical raw JSON input for `adapt_marker_output`

- `src/docforge/parsers/pdf_hybrid/engines/mineru_cli.py`
  - Resolve MinerU binary from `tools/mineru/.venv/bin/mineru`
  - Execute MinerU, write logs, write manifest
  - Determine canonical raw JSON input for `adapt_mineru_output` (prefer `*_content_list.json`)

## 3. Key design decisions
- Output paths are stable and avoid timestamps.
- `run_hash` includes:
  - pipeline version (code constant)
  - harness config (timeouts, selection weights, page range, enabled engines)
  - engine versions (derived from the engine executable)
- CI uses fixture tests only, no real engines.

## 4. Notes on repo ergonomics
- Root `.gitignore` already ignores `artifacts/` and `data/`, so local corpora and run outputs do not dirty
  git state.

