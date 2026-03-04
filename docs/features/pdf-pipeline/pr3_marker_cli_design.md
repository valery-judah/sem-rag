# Design: Marker CLI Runner

**Status:** Implemented
**Related PR:** PR3 of `docs/features/pdf-pipeline/04_workplan.md`
**Context:** `docs/features/pdf-pipeline/03_design.md`

## 1. Overview

This document specifies the design for the Marker CLI runner module and its associated shared subprocess components. These components are responsible for discovering the Marker binary, running it via subprocess with appropriate timeouts, capturing its outputs/metadata, and delegating the parsing of its raw output to the existing adapter.

This work allows `run_pdf_pipeline()` to orchestrate the Marker engine in a CI-safe, testable manner without directly embedding subprocess logic in the pipeline loop.

## 2. Components

The implementation introduces three new modules under `src/docforge/parsers/pdf_hybrid/engines/`:

1.  `_subprocess.py`: Shared subprocess execution utilities.
2.  `run_manifest.py`: Models for recording run metadata and outcomes.
3.  `marker_cli.py`: Marker-specific discovery, version detection, and execution logic.

These modules will interact with the existing `src/docforge/parsers/pdf_hybrid/engines/marker.py` module, which contains `adapt_marker_output`.

### 2.1. Shared Subprocess Utilities (`_subprocess.py`)

This internal module provides a consistent, timeout-aware wrapper around `subprocess.run()`.

**Key Responsibilities:**
*   Execute arbitrary shell commands securely (no `shell=True` unless strictly necessary for wrappers, though direct lists are preferred).
*   Enforce timeouts (via `subprocess.TimeoutExpired`).
*   Capture `stdout` and `stderr` (useful for diagnostics).
*   Handle encoding (defaulting to UTF-8).
*   Inject environment variables specifically configured for the subprocess execution.

**Proposed Interface:**
```python
from typing import Optional

class SubprocessResult:
    returncode: Optional[int]
    stdout: str
    stderr: str
    timed_out: bool
    error_message: Optional[str]

def run_command(cmd: list[str], timeout_s: float, cwd: Optional[str] = None, env: Optional[dict[str, str]] = None) -> SubprocessResult:
    """
    Executes a command and returns a normalized result, catching TimeoutExpired and other exceptions.
    Accepts optional env overrides.
    """
    pass
```

### 2.2. Run Manifest (`run_manifest.py`)

This module defines Pydantic models to standardize the metadata collected from *any* engine run (not just Marker). This acts as an intermediate structure before the pipeline constructs the final `EngineRun` for the `ExtractedPdfDocument`.

**Key Responsibilities:**
*   Standardize outcomes (`ok`, `timeout`, `error`, `unavailable`).
*   Capture engine version and binary path.
*   Record execution time.
*   Store paths to the raw outputs.

**Proposed Interface:**
```python
from pydantic import BaseModel
from typing import Optional

class EngineRunManifest(BaseModel):
    engine_name: str
    status: str  # "ok", "timeout", "error", "unavailable"
    version: Optional[str] = None
    binary_path: Optional[str] = None
    raw_output_dir: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    execution_time_s: Optional[float] = None
    error_details: Optional[str] = None
```

### 2.3. Marker CLI Module (`marker_cli.py`)

This module encapsulates all knowledge about the Marker CLI: how to find it, how to configure its execution environment, and how to execute it on a PDF.

**Key Responsibilities:**
*   **Discovery and Environment Management:**
    *   Support environment variable overrides: `DOCFORGE_MARKER_BIN` (to explicitly set the binary path) and `DOCFORGE_MARKER_VENV` (to override the default virtual environment path).
    *   Prioritize `marker_single` (which is often more stable for single-file processing). The resolution order should be:
        1. Exact path from `DOCFORGE_MARKER_BIN`
        2. `{venv_path}/bin/marker_single` (where `{venv_path}` is determined by `DOCFORGE_MARKER_VENV` or defaults to `tools/marker/.venv`)
        3. `marker_single` in `$PATH`
        4. `marker` in `$PATH`
*   **Version Detection:** Execute the discovered binary with `--version` (or similar flag, e.g., parsing help text if no version flag exists) to extract the engine version.
*   **Execution Arguments and Configuration:** 
    *   **Required Flags:** `--output_dir <dir>` and `--output_format json` must be provided.
    *   **Stability Flags:** Provide `--disable_multiprocessing True` by default to prevent hanging processes.
    *   **Performance/Feature Flags:** (Deferred) Additional optional arguments like `--disable_image_extraction`, `--page_range`, and `--processors` are not exposed in the MVP implementation.
    *   **Subprocess Environment Injection:** The runner injects specific environment variables into the `subprocess.run` call. By default, it sets `TORCH_DEVICE=cpu` and `PYTORCH_ALLOC_CONF=expandable_segments:True` unless explicitly overridden in the environment.
*   **Delegation:** Provide a convenience method to load the output JSON from disk and pass it to `marker.py::adapt_marker_output`.

**Proposed Interface:**
```python
from pathlib import Path
from docforge.parsers.pdf_hybrid.engines.run_manifest import EngineRunManifest
from docforge.parsers.pdf_hybrid.models import PageCandidate
# imports _subprocess, marker (for adapt_marker_output)

class MarkerRunner:
    def __init__(self, override_binary_path: str | None = None):
        """Initializes the runner, optionally overriding discovery."""
        pass

    def discover(self) -> str | None:
        """Finds the marker binary according to the discovery policy."""
        pass

    def get_version(self) -> str | None:
        """Returns the version of the discovered binary."""
        pass

    def is_available(self) -> bool:
        """Returns True if the binary is found."""
        pass

    def run(self, pdf_path: Path, output_dir: Path, timeout_s: float) -> EngineRunManifest:
        """
        Executes marker on the given PDF, saving outputs to output_dir.
        Returns the run manifest detailing the outcome.
        """
        pass
        
    def load_and_adapt(self, manifest: EngineRunManifest) -> list[PageCandidate]:
        """
        Loads the raw JSON from manifest.raw_output_dir and delegates to
        docforge.parsers.pdf_hybrid.engines.marker.adapt_marker_output.
        """
        pass
```

## 3. Interaction with Existing Adapter

The existing adapter (`src/docforge/parsers/pdf_hybrid/engines/marker.py`) remains structurally unchanged but requires updates to accurately locate and parse the new Marker output schema.

The `MarkerRunner.load_and_adapt` method acts as the bridge:
1.  It checks the `manifest.status`. If not `ok`, it handles the failure (e.g., returns empty candidates or raises an internal exception to be caught by the pipeline).
2.  **Output Resolution Pattern:** Marker creates a subdirectory inside `--output_dir` named after the PDF, and outputs multiple JSON files (including metadata). The runner must locate the main payload JSON file using this resolution logic:
```python
def _select_marker_json_payload(output_dir: Path) -> Path:
    candidates = [
        path for path in output_dir.rglob("*.json") 
        if not path.name.endswith("_meta.json")
    ]
    if not candidates:
        raise RuntimeError("Extractor 'marker' did not produce JSON output.")
    # Pick the largest JSON file as the main payload
    return max(candidates, key=lambda path: path.stat().st_size)
```
3.  It reads and parses the resolved JSON file using the standard `json` module.
4.  It calls `adapt_marker_output(raw_json_dict, artifact_ref=manifest.raw_output_dir)`.

### 3.1. Payload Parsing and Sanitization (for `adapt_marker_output`)
The `adapt_marker_output` function must be updated to handle Marker's output format:
*   **Two Payload Schemas:** Marker can return a "flat" payload (containing a `"blocks"` list and `"page_info"` dictionary) OR a "tree" payload (containing a `"children"` list). The downstream adapter must gracefully handle both.
*   **HTML to Plain Text Cleanup:** Marker's JSON payload often embeds text as HTML (`<br/>`, `</p>`). The adapter must run a cleanup pass replacing `<br/>` and `</p>` with newlines (`\n`), stripping all `<[^>]+>` tags, and unescaping HTML entities before yielding `PageCandidate` objects.

### 3.2. Addressing Marker Parsing Limitations (Derived from Output Verification)
Recent verification tests using `scripts/verify_targets.py` revealed several native behaviors in Marker's raw JSON output that must be explicitly handled by the adapter or the `MarkerRunner` configuration:

1. **Physical Page Indexing:** Marker operates strictly on **absolute physical page numbers**. If the pipeline relies on logical page numbers (e.g., ignoring Roman numeral prefaces), the adapter must not blindly trust the logical targets; physical offsets must be resolved either at the orchestrator level or clearly documented for consumers.
2. **Cross-Page Paragraph Fragmentation:** Marker enforces hard boundaries at the end of each page, natively splitting continuous paragraphs across pages into separate `Text` blocks. The adapter (or `distill.py` downstream) must implement a heuristic—such as checking for the absence of terminal punctuation—to merge fragmented paragraphs across `PageCandidate` boundaries.
3. **Aggressive Filtering of Floating Text (Dropped Captions):** Marker occasionally misclassifies and drops isolated text blocks, such as code snippet captions (e.g., `Listing 3.1`), likely mistaking them for headers/footers or noise. To mitigate this, `MarkerRunner` should be extended to support injecting specific layout and OCR threshold environment variables, or expose flags that disable aggressive header/footer stripping.

## 4. CI-Safe Testing Strategy

To ensure tests run reliably in CI without requiring the actual Marker binary or GPU resources, we will employ a mocking strategy focused on the `_subprocess.py` boundary.

**Testing Strategy Details:**

1.  **Mocking Subprocess:**
    In tests, we will use `unittest.mock.patch` to intercept calls to `_subprocess.run_command`.
    
2.  **Simulating Outcomes:**
    We will create parameterized tests for `MarkerRunner.run()` that mock `run_command` to return different `SubprocessResult` objects:
    *   **Success:** `returncode=0`, mock writes a dummy JSON to the output directory.
    *   **Timeout:** `timed_out=True`.
    *   **Crash:** `returncode=1`, `stderr="OOM Error"`.

3.  **Testing Discovery:**
    We will mock `os.path.exists`, `os.environ`, and `shutil.which` to test the discovery fallback logic and environment variable overrides without relying on the actual file system state.

4.  **Testing Version Detection:**
    We will mock `run_command` to return stdout matching a typical version string (e.g., `marker 0.1.0`) and verify the regex parsing logic.

5.  **Adapter Tests Remain Isolated:**
    Existing tests for `adapt_marker_output` (which use JSON fixtures) will be updated to include fixtures for both "flat" and "tree" schemas, and test the HTML sanitization logic.

## 5. Error Handling & Exceptions

The CLI module should catch `subprocess` errors and translate them into the defined taxonomy (`EngineTimeoutError`, `EngineProcessError` as mentioned in `03_design.md`), or gracefully record them in the `EngineRunManifest` status (`timeout`, `error`) so the pipeline orchestrator can continue without crashing. 

*   `timeout` -> The runner hit the `timeout_s` limit.
*   `error` -> The process crashed (return code != 0) OR the output JSON is missing/malformed.
*   `unavailable` -> `MarkerRunner.run()` was called but the binary was not discovered.
*   `ok` -> Process exited 0 and output JSON was found.