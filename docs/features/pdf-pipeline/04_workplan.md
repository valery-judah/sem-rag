# Workplan: Hybrid PDF Pipeline Wiring

**Status:** Partially Implemented  
**Last updated:** 2026-03-04

## Summary
Implement `run_pdf_pipeline()` and required wiring so that PDFs can be parsed via hybrid engines
behind a feature flag, with deterministic intermediate artifacts and stable distillation outputs.

## Reference Documents
- Context: `docs/features/pdf-pipeline/00_context.md`
- RFC (this feature): `docs/features/pdf-pipeline/01_rfc.md`
- User Stories: `docs/features/pdf-pipeline/02_user_stories.md`
- Design: `docs/features/pdf-pipeline/03_design.md`
- Test Plan: `docs/features/pdf-pipeline/05_test_plan.md`
- Rollout: `docs/features/pdf-pipeline/06_rollout.md`
- Hybrid Parsers RFC (intermediate schema, selection algorithm): `docs/features/hybrid-parsers/01_rfc.md`
- Parsers RFC (canonical `ParsedDocument` contract): `docs/features/parsers/01_rfc.md`
- E2E tooling (tool isolation + harness context): `docs/features/e2e/*`

## Current State (Repo Reality)
The repo already contains substantial hybrid-PDF scaffolding under `src/docforge/parsers/pdf_hybrid/`:

- Exists (and has tests):
  - Config: `src/docforge/parsers/pdf_hybrid/config.py`
  - Candidate + signal models: `src/docforge/parsers/pdf_hybrid/models.py`
  - Intermediate schema: `src/docforge/parsers/pdf_hybrid/schema.py`
  - Selection: `src/docforge/parsers/pdf_hybrid/selection.py`
  - Distillation: `src/docforge/parsers/pdf_hybrid/distill.py`
  - Artifact emission helpers: `src/docforge/parsers/pdf_hybrid/artifacts.py`
  - Engine output adapters (not subprocess runners):
    - `src/docforge/parsers/pdf_hybrid/engines/marker.py`
    - `src/docforge/parsers/pdf_hybrid/engines/miner_u.py`
  - Tests: `tests/parsers/pdf_hybrid/*` (adapters, selection, schema/artifacts, distill)

- Stubbed:
  - `src/docforge/parsers/pdf_hybrid/pipeline.py::run_pdf_pipeline()` currently raises `NotImplementedError`.

- Missing wiring / dependencies:
  - `ParserConfig` does not yet expose `pdf_hybrid: PdfHybridConfig` (see `src/docforge/parsers/models.py`).
  - `pypdf` is not yet a dependency (needed for deterministic `page_count` from bytes).
  - Subprocess runner layer (CLI runners, discovery, version parsing, timeouts) is not implemented.
  - Exception taxonomy for pipeline/engine failures is not implemented.
  - Default parser routing (`src/docforge/parsers/default.py`) does not yet implement stream-drain safe PDF routing
    for the hybrid path (materialize bytes once, rewrap doc for pipeline, reuse bytes on fallback).

## Locked Decisions (For This Workplan)
1. Placeholder blocks keep internal indices 0-based:
   - `page_idx` is 0-based everywhere.
   - Placeholder text is human-friendly 1-based: `[UNPARSEABLE PAGE {page_idx + 1}]`.
2. `engine_runs[].status` stays RFC-strict:
   - Keep the hybrid-parsers RFC `ok|partial|error` for schema-level status.
   - Represent runner outcomes like `timeout` / `unavailable` in `diagnostics` (or a dedicated non-contract field),
     rather than extending the public enum.

## Architecture Overview
```text
RawDocument (PDF bytes)
  -> DeterministicParser.parse() (feature flag routing)
     -> run_pdf_pipeline()
        -> Stage bytes + derive page_count (pypdf)
        -> Engine A: Marker (CLI runner)  ----\
        -> Engine B: MinerU (CLI runner) ----+-> adapt outputs (existing adapters)
                                            -> per-page selection (existing selection.py)
                                            -> ExtractedPdfDocument (existing schema.py)
                                            -> distill_pdf() (existing distill.py)
                                            -> ParsedDocument
                                            -> (optional) deterministic artifacts (existing artifacts.py)
```

## PR Plan (Phased, With Exit Criteria)

### PR1: Feature docs (this directory)
**Status:** Implemented
**Scope:**
- Ensure `docs/features/pdf-pipeline/` artifact set is complete and internally consistent.
- Cross-link to:
  - `docs/features/hybrid-parsers/01_rfc.md`
  - `docs/features/parsers/01_rfc.md`
  - `docs/features/e2e/*`

**Exit criteria:**
- Docs are internally consistent and reference intended code paths.

**Checks:**
- Docs-only.

---

### PR2: Config plumbing + stream-drain safety + `pypdf` dependency + exceptions
**Status:** Implemented
**Scope:**
- Config plumbing:
  - Add `ParserConfig.pdf_hybrid: PdfHybridConfig` with defaults.
  - Ensure hybrid settings are included in any hashing used for deterministic artifact paths (see Design).
- Stream-drain safety in `DeterministicParser.parse()`:
  - If hybrid is enabled for PDFs, materialize bytes once.
  - Rewrap `RawDocument` for pipeline call with `content_stream=iter([content_bytes])`.
  - If pipeline fails, legacy fallback MUST reuse the same already-materialized bytes.
- Add `pypdf` dependency for deterministic `page_count` and basic PDF readability checks.
- Add explicit exceptions (new module):
  - `src/docforge/parsers/pdf_hybrid/exceptions.py` (taxonomy described in `03_design.md`).

**Touched modules (expected):**
- `src/docforge/parsers/models.py` (ParserConfig)
- `src/docforge/parsers/default.py` (routing + stream safety)
- `src/docforge/parsers/pdf_hybrid/exceptions.py` (new)
- `pyproject.toml` (+ `uv.lock` via `uv` workflow) to add `pypdf`
- Tests:
  - Add a test that fails pipeline but still produces non-empty legacy fallback due to safe byte reuse.

**Exit criteria:**
- Hybrid path no longer risks draining the PDF stream and breaking fallback parsing.
- `ParserConfig.pdf_hybrid` exists and has stable defaults.
- `pypdf` is available and `page_count` source-of-truth is defined.
- Exception hierarchy importable and used by pipeline/runner code (as it lands).

**Checks:**
- `make fmt`, `make lint`, `make type`, `make test`.

---

### PR3: Subprocess runner layer (tools isolation) without moving adapters
**Status:** Partially Implemented (Marker CLI completed, MinerU CLI pending)
**Scope:**
- Add CLI runner modules under `src/docforge/parsers/pdf_hybrid/engines/`:
  - `_subprocess.py` (shared subprocess utilities) - **Completed**
  - `run_manifest.py` (run metadata) - **Completed**
  - `marker_cli.py` (Marker discovery/version/run) - **Completed**
  - `mineru_cli.py` (MinerU discovery/version/run) - *Pending*
- Keep existing adapters in place:
  - `src/docforge/parsers/pdf_hybrid/engines/marker.py::adapt_marker_output` - **Completed**
  - `src/docforge/parsers/pdf_hybrid/engines/miner_u.py::adapt_mineru_output` - *Pending integration*
  - The new `*_cli.py` modules should load raw outputs and call these adapters.
- Discovery policy follows `03_design.md` / `01_rfc.md`:
  - Prefer `tools/marker/.venv/bin/marker_single` then fallback to `marker` on PATH.
  - Prefer `tools/mineru/.venv/bin/mineru`.
  - Note: `tools/` may be created/provisioned by the separate E2E effort; runner code must handle
    missing `tools/` gracefully.
- Implement timeouts/version detection in a CI-safe way (mock subprocess in unit tests).

**Exit criteria:**
- Runner code unit-tested without requiring real engines.
- Engine discovery/version detection returns `None` when missing (no crashes).
- Timeout/process failures become structured runner outcomes (recorded in manifests/diagnostics).

**Checks:**
- `make fmt`, `make lint`, `make type`, `make test`.

---

### PR4: Implement `run_pdf_pipeline()` + artifact emission + determinism tests (CI-safe)
**Scope:**
- Implement `src/docforge/parsers/pdf_hybrid/pipeline.py::run_pdf_pipeline()`:
  - Drain bytes, compute `content_hash`.
  - Determine `page_count` from `pypdf` (not from engine outputs).
  - Resolve stable artifact directories and stable `run_id` (no timestamps).
  - Stage PDF to a temp path for engine CLIs.
  - Execute engines (sequential MVP, parallel later as a follow-up).
  - Adapt outputs using existing adapter functions and normalize into `page_candidates`.
  - Run selection (existing `selection.py`) and assemble `ExtractedPdfDocument` (existing `schema.py`).
  - Emit deterministic artifacts when enabled:
    - `selection_log.jsonl`
    - `extracted_pdf_document.json`
    - `parsed_document.json` (via `distill_pdf`)
  - Ensure temp files are cleaned up via context manager/finally.
- Implement determinism tests:
  - With fixed inputs and mocked runner outputs, emitted artifacts must be byte-identical across runs.

**Exit criteria:**
- CI tests pass without real engines (mock/inject runners).
- Extracted intermediate validates and distillation produces a valid `ParsedDocument`.
- Artifacts are stable and reproducible for identical inputs/config.

**Checks:**
- `make fmt`, `make lint`, `make type`, `make test`.

---

### PR5: Local-only smoke workflow (not in CI)
**Scope:**
- Add `docs/features/pdf-pipeline/LOCAL_SMOKE.md` documenting:
  - Provisioning `tools/marker` and `tools/mineru` envs (or referencing the E2E provisioning doc if that becomes
    the source of truth).
  - A minimal local run command and the expected artifact outputs.
  - Troubleshooting notes (timeouts, missing binaries/models, OOM).

**Exit criteria:**
- On a machine with tool envs provisioned, hybrid parsing produces expected artifacts and a valid parsed output.

**Checks:**
- `make test` (CI) and manual smoke run documented.

## Dependency Graph
```text
PR1 (docs)
  -> PR2 (config + stream safety + pypdf + exceptions)
    -> PR3 (subprocess runners)
      -> PR4 (pipeline + artifacts + determinism)
        -> PR5 (local smoke)
```

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Pipeline PR is too large | Split into pipeline assembly vs artifact emission vs determinism tests |
| Engine output schemas change | Keep adapters unit-tested; pin versions for local tooling; update fixtures when needed |
| Timeout tuning varies by hardware | Make timeouts configurable; document recommended values in LOCAL_SMOKE.md |
| Large-PDF memory pressure | Document size limits; keep staged artifacts for debugging; consider future streaming |
| Placeholder semantics drift | Lock placeholder text/indexing in tests (page_idx 0-based; text uses page_idx + 1) |

## Definition of Done
- [ ] `run_pdf_pipeline()` implemented and deterministic for identical inputs/config.
- [ ] Feature-flagged PDF parsing yields a valid `ParsedDocument` via hybrid pipeline when enabled.
- [ ] Intermediate schema (`ExtractedPdfDocument`) validates and matches the hybrid-parsers RFC.
- [ ] Artifacts (when enabled) are reproducible and provenance-complete.
- [ ] Placeholder blocks emitted deterministically for pages where all engines fail:
  - `page_idx` stays 0-based
  - text uses `[UNPARSEABLE PAGE {page_idx + 1}]`
- [ ] Engine run status stays RFC-strict `ok|partial|error`; timeout/unavailable captured in diagnostics.
- [ ] No real-engine dependency in CI tests (mock/inject runners).
- [ ] Local smoke path documented and validated manually.

