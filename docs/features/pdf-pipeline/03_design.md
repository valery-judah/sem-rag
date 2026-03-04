# Design: run_pdf_pipeline() Wiring

**Status:** Partially Implemented
**Last updated:** 2026-03-04

## 1. Entry points
- `src/docforge/parsers/default.py::DeterministicParser.parse()` routes PDFs to pipeline when enabled.
- `src/docforge/parsers/pdf_hybrid/pipeline.py::run_pdf_pipeline()` coordinates execution and assembly.

## 2. Required supporting modules
Add internal runner modules (shared with the E2E harness):
- `src/docforge/parsers/pdf_hybrid/engines/_subprocess.py`
- `src/docforge/parsers/pdf_hybrid/engines/run_manifest.py`
- `src/docforge/parsers/pdf_hybrid/engines/marker_cli.py`
- `src/docforge/parsers/pdf_hybrid/engines/mineru_cli.py` (Pending/Deferred to later PR)

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
6. Run engines sequentially (MVP):
   - Marker runner writes into `doc_dir/engine_artifacts/marker/`
   - MinerU runner writes into `doc_dir/engine_artifacts/mineru/`
   - Capture stdout/stderr for debugging.
   - Apply per-engine timeouts (`marker_timeout_s`, `mineru_timeout_s`).
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

## 5. Error handling policy (normative)

### 5.1 Exception taxonomy
Define explicit exception types in `src/docforge/parsers/pdf_hybrid/exceptions.py`:

| Exception | Raised when | Caller action |
|-----------|-------------|---------------|
| `PdfHybridPipelineUnavailable` | `require_any_engine=True` and no engine binary is discoverable | Parser falls back to legacy |
| `EngineTimeoutError` | Engine subprocess exceeds configured timeout | Recorded in `engine_runs[].status`; pipeline continues |
| `EngineProcessError` | Engine subprocess exits non-zero or crashes | Recorded in `engine_runs[].status`; pipeline continues |
| `AdapterParseError` | Engine output JSON is malformed or schema-invalid | Treated as engine failure for that run |

### 5.2 Engine availability (pre-flight)
Before running engines:
1. Probe for Marker binary at `tools/marker/.venv/bin/marker_single` (fallback: `marker` on PATH).
2. Probe for MinerU binary at `tools/mineru/.venv/bin/mineru`.
3. Record availability in `engine_availability: dict[str, bool]`.

Policy (per RFC §6):
- If `require_any_engine=True` (default) and **no engine** is available → raise `PdfHybridPipelineUnavailable`.
- If at least one engine is available → proceed; treat unavailable engine as status `unavailable` in `engine_runs[]`.

### 5.3 Per-engine run failures
Each engine run records a status:
- `ok`: completed successfully with parseable output.
- `timeout`: exceeded `{engine}_timeout_s`.
- `error`: non-zero exit, crash, or adapter parse failure.
- `unavailable`: engine binary not found (skipped).

A failed engine run does **not** abort the pipeline. The selection stage will handle missing candidates.

### 5.4 Per-page failure handling
During selection (per RFC §8.3 and §13):
- If **both** candidates for a page have status in `{empty, error, timeout, unavailable}`:
  - Mark page as **failed**.
  - Emit a deterministic **placeholder block**:
    ```json
    {
      "block_id": "placeholder_{page_idx}",
      "type": "unknown",
      "text": "[UNPARSEABLE PAGE {page_idx + 1}]",
      "page_idx": page_idx,
      "reading_order_key": "0000",
      "source": { "engine": "placeholder", "engine_artifact_ref": null },
      "confidence": 0.0,
      "metadata": { "placeholder_reason": "all_engines_failed" }
    }
    ```
  - Record `selection_reason = "placeholder:all_engines_failed"`.

### 5.5 Document-level failure escalation
The pipeline escalates to a hard failure **only** when:
- `PdfHybridPipelineUnavailable` is raised (no engines at all).
- `pypdf` cannot read the PDF (corrupt/encrypted) → raise `PdfHybridPipelineError("unreadable_pdf")`.

Partial page failures (even all pages) do **not** fail the document; the result will contain only placeholder blocks.

### 5.6 Cleanup on failure
- Temp files (staged PDF) MUST be cleaned up in a `finally` block or context manager.
- Partial artifacts in `doc_dir/` are retained for debugging (they are gitignored).

## 6. Determinism details
- Fixed engine order: marker, then mineru.
- Stable selection and tie-breakers are already implemented in `selection.py`.
- JSON emission:
  - Use pydantic `.model_dump_json(...)` consistently and ensure stable list ordering (sort pages by idx).
  - No timestamps inside JSON.

## 7. Engine availability policy
- If `require_any_engine=True` and neither engine is runnable, raise `PdfHybridPipelineUnavailable`.
- If one engine is runnable, proceed and treat the other as status `unavailable` in `engine_runs[]`.

---

## 8. Future enhancement: Parallel engine execution

> **Note:** This section describes a post-MVP optimization. The MVP runs engines sequentially to simplify error handling and debugging.

### 8.1 Rationale
Marker and MinerU run as independent subprocesses with separate resource requirements. Running them in parallel can reduce wall-clock time by up to ~50% for large documents.

### 8.2 Implementation approach
Replace step 6 in the pipeline algorithm with:
