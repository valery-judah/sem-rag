# RFC: Hybrid PDF Pipeline Wiring (Marker + MinerU subprocess, tools isolation)

**Status:** Draft
**Last updated:** 2026-03-04

## 1. Scope
This RFC defines the wiring required to implement `run_pdf_pipeline()`:
- Execute Marker and MinerU via subprocess CLIs in isolated tool environments.
- Adapt engine outputs into shared candidate models.
- Run deterministic selection and placeholder policy.
- Assemble `ExtractedPdfDocument` (per `docs/features/hybrid-parsers/01_rfc.md` Section 9).
- Optionally emit deterministic artifacts (default ON).
- Return `ExtractedPdfDocument` for distillation into canonical `ParsedDocument`.

This RFC does not redefine the hybrid-parsers contract; it references it.

## 2. Normative dependencies and isolation
- Add `pypdf` as a core dependency to determine `page_count` deterministically from PDF bytes.
- Engines MUST run from isolated tool projects:
  - `tools/marker/.venv/bin/marker_single` preferred (fallback `marker`)
  - `tools/mineru/.venv/bin/mineru`

## 3. Public configuration surface (normative)
`ParserConfig` MUST expose hybrid settings:
- `ParserConfig.pdf_hybrid: PdfHybridConfig` (default_factory)

`PdfHybridConfig` MUST include:
- `marker_timeout_s: int`
- `mineru_timeout_s: int`
- `selection_weights: SelectionWeights`
- `force_engine: str | None`
- `emit_artifacts: bool = True`
- `artifact_dir: str = "artifacts/pdf_hybrid_pipeline"` (default ON; safe because `artifacts/` is gitignored)
- `parallel_engines: bool = True`
- `require_any_engine: bool = True` (if no engines are available, raise and allow parser fallback)

Optional overrides (allowed but must be included in config_hash if used):
- explicit engine binary paths
- MinerU runtime knobs (dictionary-based models-dir, device, -b pipeline backend)

## 4. Artifact layout (normative)
Artifacts are written under:
- `<artifact_dir>/<safe_doc_id>/<run_id>/`

Where:
- `safe_doc_id` is `doc.doc_id` if filesystem-safe else `sha256(doc.doc_id)[:32]`.
- `content_hash = sha256(pdf_bytes)` (hex, full length stored in intermediate).
- `config_hash = sha256(canonical_json({pipeline_version, pdf_hybrid_config, engine_versions, engine_runtime_overrides}))`
  (full hex stored in intermediate).
- `run_id = "{pipeline_version}_{content_hash[:16]}_{config_hash[:16]}"` (stable; no timestamps).

Required outputs when `emit_artifacts=True`:
- `engine_artifacts/marker/...` (if executed)
- `engine_artifacts/mineru/...` (if executed)
- `selection_log.jsonl`
- `extracted_pdf_document.json`
- `parsed_document.json`

## 5. Page count source of truth (normative)
`page_count` MUST come from `pypdf` reading the input bytes. Engine outputs MUST NOT be the source
of truth for `page_count`.

## 6. Failure policy (normative)
- If at least one engine is available, proceed best-effort and emit placeholders for pages where
  all engines fail.
- If no engines are available, raise a pipeline-unavailable error; the caller may fall back to legacy
  behavior.
- Partial engine failures MUST NOT fail the entire document by default.

## 7. Determinism (normative)
- No timestamps in emitted artifacts.
- Stable ordering for:
  - pages by `page_idx`
  - engines by fixed priority order (`marker`, `mineru`)
  - candidates by `reading_order_key` (required by the hybrid-parsers RFC)
- Any output-affecting config/runtime knob MUST be included in `config_hash`.

