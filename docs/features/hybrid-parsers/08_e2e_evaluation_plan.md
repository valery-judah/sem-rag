# End-to-End Parser Evaluation Pipeline Design

To run the pipeline against all files in a `data` directory while ensuring install isolation for heavy dependency parsers like MinerU and Marker, I propose the following design:

## 1. Architecture & Install Isolation
Machine learning-based parsers often have conflicting dependencies (e.g., PyTorch versions, CUDA bindings, or specific PDF libraries). To prevent polluting the main `docforge` environment:
- **Isolated Virtual Environments:** We will use `uv venv` to create dedicated environments for each engine outside the main project dependencies:
  - `.venvs/mineru/` for `mineru[all]`
  - `.venvs/marker/` for `marker-pdf[full]`
- **Execution Strategy:** Instead of using `uv run` (which targets the project's `pyproject.toml`), the pipeline will execute the engines using their isolated binaries directly (e.g., `.venvs/mineru/bin/mineru`). This ensures true isolation while allowing the orchestration script to run from the main project environment safely.

## 2. Pipeline Orchestration (`scripts/e2e_parser_eval.py`)
A new orchestration script will coordinate the end-to-end evaluation:

**Phase A: Environment Provisioning**
- The script checks if `.venvs/<engine>` exists. If missing or if a `--reinstall` flag is passed, it automatically provisions the environment:
  ```bash
  uv venv .venvs/<engine> --allow-existing
  uv pip install --python .venvs/<engine>/bin/python "<engine_package_name>"
  ```

**Phase B: Data Discovery**
- Dynamically scans the `data/` directory (or a user-provided `--data-dir`) for all `.pdf` files.

**Phase C: Execution Loop**
- Iterates over each discovered PDF file and chosen engine.
- For each combination, invokes the isolated CLI as a subprocess, saving outputs to a structured directory: `artifacts/e2e_eval/<run_id>/<engine>/<pdf_stem>/`.

**Phase D: End-to-End Validation (The "Contract" Check)**
- *Crucial Step:* Running the CLI alone is insufficient to guarantee stability. The script must validate that the output produced by the engine still conforms to our internal `docforge` schema.
- It loads the raw output JSON (e.g., MinerU's `_content_list.json` or Marker's `children` JSON).
- It dynamically imports and runs our internal adapters (like `src/docforge/parsers/pdf_hybrid/engines/miner_u.py::adapt_mineru_output` and `marker.py::adapt_marker_output`).
- It asserts that `PageCandidate` and `BlockCandidate` models are successfully populated without validation errors, proving the external tool's API hasn't drifted or broken our integration.

**Phase E: Reporting**
- Generates a summary matrix (Success / Fail / Empty / SchemaError) for each file across all engines.
- Outputs a console table and a `summary.json` containing metrics like time taken, page counts, and extracted block/asset counts.

## 3. Refactoring Existing Scripts
- **Update `test_mineru.py`:** Stop using `uv add mineru[all]` (which pollutes the global `uv.lock` and main project environment). It should adopt the `.venvs/mineru` isolation approach immediately to mirror the Marker setup.
- **Makefile Integration:** Add a new target `make test-e2e DATA_DIR=data/` to provide developers with a standard entry point for running the test suite.

This design guarantees that any upstream changes to third-party engines or local changes to our internal schemas are caught immediately against a real-world dataset, without risking dependency conflicts in the core repository environment.