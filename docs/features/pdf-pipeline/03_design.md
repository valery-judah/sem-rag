# Design: run_pdf_pipeline() Wiring

**Status:** Draft
**Last updated:** 2026-03-04

## 1. Entry points
- `src/docforge/parsers/default.py::DeterministicParser.parse()` routes PDFs to pipeline when enabled.
- `src/docforge/parsers/pdf_hybrid/pipeline.py::run_pdf_pipeline()` coordinates execution and assembly.

## 2. Required supporting modules
Add internal runner modules (shared with the E2E harness):
- `src/docforge/parsers/pdf_hybrid/engines/_subprocess.py`
- `src/docforge/parsers/pdf_hybrid/engines/run_manifest.py`
- `src/docforge/parsers/pdf_hybrid/engines/marker_cli.py`
- `src/docforge/parsers/pdf_hybrid/engines/mineru_cli.py`

## 3. Stream-drain safe routing (required)
Because `RawDocument.content_stream` can be drained once:
- `DeterministicParser.parse()` MUST materialize bytes once for PDFs when hybrid is enabled.
- It MUST pass a re-wrapped `RawDocument` (with `content_stream=iter([content_bytes])`) into
  `run_pdf_pipeline()`.
- If pipeline fails, legacy fallback MUST reuse the already materialized bytes.

## 4. Pipeline algorithm (concrete)
Given `(doc, config)`:
1. Drain bytes from `content_stream`.
2. Compute `content_hash`.
3. Compute `page_count` from `pypdf.PdfReader`.
4. Resolve output dirs:
   - `artifact_root = config.pdf_hybrid.artifact_dir`
   - `run_id = "{pipeline_version}_{content_hash[:16]}_{config_hash[:16]}"`
   - `doc_dir = <artifact_root>/<safe_doc_id>/<run_id>/`
5. Stage PDF to a temp dir path for engine CLIs.
6. Run engines:
   - Marker runner writes into `doc_dir/engine_artifacts/marker/`
   - MinerU runner writes into `doc_dir/engine_artifacts/mineru/`
   - Capture stdout/stderr for debugging.
   - Apply per-engine timeouts.
7. Load raw outputs and adapt:
   - `adapt_marker_output(raw_marker_json, artifact_ref)`
   - `adapt_mineru_output(raw_mineru_json, artifact_ref)`
8. Normalize candidates into `page_candidates[page_idx][engine]` for all pages `0..page_count-1`.
9. Run selection: `run_selection(page_candidates, pdf_hybrid_config)`.
10. Assemble `ExtractedPdfDocument` with:
   - `source_pdf.content_hash`, `source_pdf.page_count`, `pipeline.pipeline_version`, `pipeline.config_hash`
   - `engine_runs[]` including `engine_version` and `engine_config_hash`
   - `pages[]` including `selected_engine` and `selection_reason`
11. Emit artifacts if enabled:
   - `selection_log.jsonl`
   - `extracted_pdf_document.json`
   - `parsed_document.json` (via `distill_pdf`)
12. Return `ExtractedPdfDocument`.

## 5. Determinism details
- Fixed engine order: marker, then mineru.
- Stable selection and tie-breakers are already implemented in `selection.py`.
- JSON emission:
  - Use pydantic `.model_dump_json(...)` consistently and ensure stable list ordering (sort pages by idx).
  - No timestamps inside JSON.

## 6. Engine availability policy
- If `require_any_engine=True` and neither engine is runnable, raise a dedicated
  `PdfHybridPipelineUnavailable` exception.
- If one engine is runnable, proceed and treat the other as a failed engine run.

