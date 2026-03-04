# RFC: Local E2E Evaluation Harness (Hybrid PDF)

**Status:** Draft
**Last updated:** 2026-03-04

## 1. Scope
This RFC defines a reproducible local harness that:
- Runs Marker and/or MinerU against PDFs in local `data/`.
- Validates adapter normalization using `docforge.parsers.pdf_hybrid.engines.*.adapt_*`.
- Runs deterministic selection and emits required pipeline artifacts.
- Runs distillation into canonical `ParsedDocument` and validates invariants.

This RFC does not change the canonical `ParsedDocument` contract.

## 2. Determinism and Stability Goals
Non-negotiables (from `docs/agentic-docs/00_playbook.md`):
- Stable identity for produced artifacts when inputs and config are unchanged.
- Provenance from derived artifacts back to source representation.
- Determinism for identical inputs, code version, engine versions, and config.

## 3. Install Isolation (Normative)
The harness MUST avoid polluting the root project dependencies.

We standardize on tool subprojects with independent lockfiles:
- `tools/marker/pyproject.toml` + `tools/marker/uv.lock`
- `tools/mineru/pyproject.toml` + `tools/mineru/uv.lock`

Tool provisioning is via:
- `uv sync --project tools/marker`
- `uv sync --project tools/mineru`

Engine binaries MUST be resolved from those tool venvs by default.

## 4. Inputs
- Default data directory: `data/`
- Default file match: `*.pdf`
- `data/` is expected to be gitignored and local-only.

## 5. Artifact Identity and Layout (Normative)
Per input PDF:
1. Compute `content_hash = sha256(pdf_bytes).hexdigest()`.
2. Define stable `doc_id = "pdf_" + content_hash[:16]`.

Define a stable run signature:
- `run_hash = sha256(canonical_json({pipeline_version, harness_config, engine_versions})).hexdigest()[:16]`

All outputs go to:
- `artifacts/pdf_hybrid_e2e/<doc_id>/<run_hash>/`

Within that directory, the harness MUST write:
- `engine_artifacts/marker/<doc_id>/...` (if executed)
- `engine_artifacts/mineru/<doc_id>/...` (if executed)
- `selection_log.jsonl`
- `extracted_pdf_document.json`
- `parsed_document.json`
- `summary.json`

RFC alignment:
- `engine_artifact_ref` fields in intermediate outputs MUST be stable pointers into
  the above artifact directories.

## 6. CI Policy (Normative)
CI MUST NOT require real engines.
CI SHOULD test harness logic using synthetic fixtures, including:
- manifest schema roundtrip
- path derivation and discovery logic
- intermediate assembly edge cases

## 7. Out of Scope
- Any requirement that Marker/MinerU run in CI.
- External model downloads (the harness may warn and exit with instructions).

