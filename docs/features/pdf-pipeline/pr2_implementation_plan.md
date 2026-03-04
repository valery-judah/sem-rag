# PR2 Implementation Plan: Config plumbing + stream-drain safety + pypdf + exceptions

**Status:** Implemented (as of 2026-03-04)
**Goal:** Complete PR2 scope from `04_workplan.md`.

## Checklist
- [x] Add `pypdf` dependency + lockfile update
- [x] Add PDF hybrid pipeline exception taxonomy
- [x] Add `ParserConfig.pdf_hybrid` + deterministic `config_hash`
- [x] Ensure stream-drain safety + safe fallback semantics
- [x] Add/adjust tests and validation commands

## Step 1: Add Dependency ✅
- **Files:** `pyproject.toml`, `uv.lock`
- **Action:** Add `"pypdf>=5.0.0"` to the dependencies list and update the lockfile.
- **Notes:** `pypdf` is present in `pyproject.toml`, and `uv.lock` includes a resolved `pypdf` entry.

## Step 2: Create Exception Taxonomy ✅
- **File:** `src/docforge/parsers/pdf_hybrid/exceptions.py`
- **Action:** Define the following exception classes (inheriting appropriately, e.g., from a base `PdfHybridPipelineError`):
  - `PdfHybridPipelineError(Exception)`: Base exception for hybrid pipeline errors.
  - `PdfHybridPipelineUnavailable(PdfHybridPipelineError)`: Raised when `require_any_engine=True` and no engine binary is discoverable.
  - `EngineTimeoutError(PdfHybridPipelineError)`: Raised when an engine subprocess exceeds configured timeout.
  - `EngineProcessError(PdfHybridPipelineError)`: Raised when an engine subprocess exits non-zero or crashes.
  - `AdapterParseError(PdfHybridPipelineError)`: Raised when engine output JSON is malformed or schema-invalid.

## Step 3: Update `ParserConfig` and Config Hashing ✅
- **File:** `src/docforge/parsers/models.py`
- **Actions:**
  - Import `PdfHybridConfig` from `docforge.parsers.pdf_hybrid.config`.
  - Add `pdf_hybrid: PdfHybridConfig = Field(default_factory=PdfHybridConfig)` to the `ParserConfig` model.
  - Add a `@property` named `config_hash` to `ParserConfig`. This method should:
    - Serialize the config to a dictionary using `self.model_dump(mode="json")`.
    - Dump the dictionary to a JSON string with `json.dumps(..., sort_keys=True)` to ensure deterministic ordering.
    - Return a SHA-256 hash of the utf-8 encoded JSON string.
- **Correction (important):** Ensure `PdfHybridConfig` (and nested submodels like selection weights) are also strict/extra-forbid so typos or unknown keys under `pdf_hybrid` cannot be silently ignored (and so config hashing/caching remains trustworthy).

## Step 4: Stream-drain Safety in `DeterministicParser.parse()` ✅
- **File:** `src/docforge/parsers/default.py`
- **Actions:**
  - Modify `DeterministicParser.parse()` to materialize PDF bytes *before* passing the document to `run_pdf_pipeline()`.
  - If `doc.content_type == "application/pdf"` and `enable_hybrid_pdf_pipeline` is true:
    - `content_bytes = self._materialize_content(doc)`
    - Create a copy of the document for the pipeline with a fresh iterator: `pipeline_doc = doc.model_copy(update={"content_stream": iter([content_bytes])})`.
    - Pass `pipeline_doc` to `run_pdf_pipeline()`.
    - Catch only expected fallback conditions (e.g., `NotImplementedError` while the pipeline is stubbed, and `PdfHybridPipelineError` for known pipeline failure modes) and set `pdf_hybrid_fallback = True`.
    - Do **not** catch generic `Exception`, so unexpected regressions/invariant violations surface loudly.
  - Ensure the fallback parsing path uses the already `content_bytes` if they were materialized, avoiding a second call to `_materialize_content(doc)` that would yield empty bytes.

## Step 5: Testing and Validation ✅
- **File:** `tests/parsers/test_models.py`
  - **Action:** Add tests for `ParserConfig` to ensure `pdf_hybrid` defaults correctly and `config_hash` returns a stable, deterministic hash across identical config states.
- **Correction (important):** Add tests that `pdf_hybrid` rejects unknown keys (typos) and rejects type coercions in strict mode (e.g., `"120"` for an `int`).
- **File:** `tests/parsers/test_default_parser.py`
  - **Action:** Add a test verifying stream-drain safety. The test should mock `run_pdf_pipeline` to raise an exception, and assert that the legacy fallback successfully parses the reused bytes instead of receiving an empty stream.
- **Correction (important):**
  - Assert `run_pdf_pipeline` is called with `parser.config` (wiring guarantee).
  - Add a test that unexpected exceptions from `run_pdf_pipeline` propagate (only known pipeline errors should trigger fallback).
- **CLI Commands:**
  - Run `make fmt`, `make lint`, `make type`, and `make test` to ensure all checks pass.
