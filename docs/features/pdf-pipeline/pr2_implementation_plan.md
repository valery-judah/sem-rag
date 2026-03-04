# PR2 Implementation Plan: Config plumbing + stream-drain safety + pypdf + exceptions

**Status:** Ready for Implementation
**Goal:** Complete PR2 scope from `04_workplan.md`.

## Step 1: Add Dependency
- **File:** `pyproject.toml`
- **Action:** Add `"pypdf>=5.0.0"` to the `dependencies` list.
- **CLI Command:** Run `make sync` (or `uv sync` / `uv lock`) to update the `uv.lock` file.

## Step 2: Create Exception Taxonomy
- **File:** `src/docforge/parsers/pdf_hybrid/exceptions.py` (New File)
- **Action:** Create the file and define the following exception classes (inheriting appropriately, e.g., from a base `PdfHybridPipelineError`):
  - `PdfHybridPipelineError(Exception)`: Base exception for hybrid pipeline errors.
  - `PdfHybridPipelineUnavailable(PdfHybridPipelineError)`: Raised when `require_any_engine=True` and no engine binary is discoverable.
  - `EngineTimeoutError(PdfHybridPipelineError)`: Raised when an engine subprocess exceeds configured timeout.
  - `EngineProcessError(PdfHybridPipelineError)`: Raised when an engine subprocess exits non-zero or crashes.
  - `AdapterParseError(PdfHybridPipelineError)`: Raised when engine output JSON is malformed or schema-invalid.

## Step 3: Update `ParserConfig` and Config Hashing
- **File:** `src/docforge/parsers/models.py`
- **Actions:**
  - Import `PdfHybridConfig` from `docforge.parsers.pdf_hybrid.config`.
  - Add `pdf_hybrid: PdfHybridConfig = Field(default_factory=PdfHybridConfig)` to the `ParserConfig` model.
  - Add a `@property` named `config_hash` to `ParserConfig`. This method should:
    - Serialize the config to a dictionary using `self.model_dump(mode="json")`.
    - Dump the dictionary to a JSON string with `json.dumps(..., sort_keys=True)` to ensure deterministic ordering.
    - Return a SHA-256 hash of the utf-8 encoded JSON string.

## Step 4: Stream-drain Safety in `DeterministicParser.parse()`
- **File:** `src/docforge/parsers/default.py`
- **Actions:**
  - Modify `DeterministicParser.parse()` to materialize PDF bytes *before* passing the document to `run_pdf_pipeline()`.
  - If `doc.content_type == "application/pdf"` and `enable_hybrid_pdf_pipeline` is true:
    - `content_bytes = self._materialize_content(doc)`
    - Create a copy of the document for the pipeline with a fresh iterator: `pipeline_doc = doc.model_copy(update={"content_stream": iter([content_bytes])})`.
    - Pass `pipeline_doc` to `run_pdf_pipeline()`.
    - Use a generic `except Exception:` block around `run_pdf_pipeline` to catch `NotImplementedError` or new pipeline exceptions, setting `pdf_hybrid_fallback = True`.
  - Ensure the fallback parsing path uses the already `content_bytes` if they were materialized, avoiding a second call to `_materialize_content(doc)` that would yield empty bytes.

## Step 5: Testing and Validation
- **File:** `tests/parsers/test_models.py`
  - **Action:** Add tests for `ParserConfig` to ensure `pdf_hybrid` defaults correctly and `config_hash` returns a stable, deterministic hash across identical config states.
- **File:** `tests/parsers/test_default_parser.py`
  - **Action:** Add a test verifying stream-drain safety. The test should mock `run_pdf_pipeline` to raise an exception, and assert that the legacy fallback successfully parses the reused bytes instead of receiving an empty stream.
- **CLI Commands:**
  - Run `make fmt`, `make lint`, `make type`, and `make test` to ensure all checks pass.
