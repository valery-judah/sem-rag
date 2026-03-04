# Workplan: Hybrid PDF E2E Evaluation Harness

**Status:** Draft
**Last updated:** 2026-03-04

## Summary
Add a local, real-engine end-to-end evaluation harness that runs Marker and MinerU against PDFs in `data/`
(gitignored), produces RFC-aligned artifacts, and validates adapters + selection + distillation deterministically.
Use install isolation via `tools/` subprojects with per-tool `uv.lock`. CI remains fixture-only.

## Scope and Non-goals
### In scope
- `make e2e-pdf` local harness.
- Tool isolation via `tools/marker` and `tools/mineru`.
- Engine runner library code that emits `run_manifest.json`.
- Artifact identity and provenance consistent with `docs/features/hybrid-parsers/01_rfc.md`.

### Out of scope
- Real engines in CI.
- Quality KPIs as merge gates.
- Implementing `run_pdf_pipeline()` wiring.

## Public Interfaces
- Make targets:
  - `make tools-sync`
  - `make e2e-pdf`
- Script:
  - `scripts/e2e_hybrid_pdf_eval.py`

## Artifact Layout (Normative)
Per PDF:
- `doc_id = "pdf_" + sha256(pdf_bytes)[:16]`
- `run_hash = sha256(canonical_json({pipeline_version, harness_config, engine_versions}))[:16]`

Output root:
- `artifacts/pdf_hybrid_e2e/<doc_id>/<run_hash>/`

Required outputs in that directory:
- `engine_artifacts/marker/<doc_id>/...` (if executed)
- `engine_artifacts/mineru/<doc_id>/...` (if executed)
- `selection_log.jsonl`
- `extracted_pdf_document.json`
- `parsed_document.json`
- `summary.json`

## Install Isolation (Normative)
- `tools/marker/pyproject.toml` + `tools/marker/uv.lock`
- `tools/mineru/pyproject.toml` + `tools/mineru/uv.lock`
- Provision with `uv sync --project ...`

## PR Plan (Phased)

### PR1: E2E Feature Docs
Scope:
- Add `docs/features/e2e/` feature artifact set (this directory).
- Update `docs/features/hybrid-parsers/08_e2e_evaluation_plan.md` to point here and avoid cross-repo confusion.

Exit criteria:
- Docs are internally consistent and link to existing hybrid-parsers RFC and this repo’s Makefile conventions.

Required checks:
- Docs-only (no mandatory runtime checks).

### PR2: Tool Subprojects + Make Targets (Isolation)
Scope:
- Add `tools/marker` and `tools/mineru` subprojects with pinned deps and `uv.lock`.
- Add Make targets: `tools-sync`, `tool-marker-sync`, `tool-mineru-sync`.

Exit criteria:
- Tools provision reproducibly and do not modify the root `pyproject.toml` or root `uv.lock`.

Required checks:
- Code/config change: run `make test`.

### PR3: Engine Runner Library (Manifests, Discovery, Timeouts)
Scope:
- Add internal runner modules and manifest schema:
  - `run_manifest.py`, `marker_cli.py`, `mineru_cli.py`
- Add unit tests that do not require real engines.

Exit criteria:
- Manifest schema is stable and output discovery logic is tested.

Required checks:
- `make fmt`, `make lint`, `make type`, `make test`.

### PR4: E2E Harness Script + Minimal Non-engine Tests
Scope:
- Add `scripts/e2e_hybrid_pdf_eval.py`.
- Add `make e2e-pdf` target.
- Add tests for stable doc_id/run_hash derivation and intermediate assembly edge cases.

Exit criteria:
- Local run on a machine with tools provisioned and local `data/` PDFs produces required artifacts per doc.

Required checks:
- `make fmt`, `make lint`, `make type`, `make test`.

## Test Scenarios
- Both engines available, multiple PDFs: artifacts emitted and `ParsedDocument` validates.
- Only one engine available: still emits deterministic placeholders and writes outputs.
- Missing `data/`: non-zero exit with actionable instructions.
- Timeout configured small: timeouts recorded; artifacts still emitted.

## Defaults and Assumptions
- Sem-rag only (no coordinated changes in `/Users/val/projects/rag/parsers`).
- CI is fixture-only for this harness.
- Default engines are Marker and MinerU only.
- MinerU model downloads are not automated by the harness.

