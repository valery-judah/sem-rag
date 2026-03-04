# Scripts Directory

This directory contains utility scripts for ad-hoc testing, verification, and debugging. These scripts are not part of the main application code or the test suite but are useful for developers working on the project.

## Setting up External Tools

Some components of this project (like advanced PDF parsers) rely on external tools with heavy dependencies (e.g., PyTorch, `marker-pdf`). **Do not install these heavy dependencies into the main project environment**, as it will slow down CI and make the core environment unnecessarily large.

Instead, we use isolated virtual environments for these tools, typically stored in the `tools/` directory.

### Example: Setting up `marker-pdf`

To set up the `marker-pdf` engine locally for testing:

1. Create the `tools/marker` directory if it doesn't exist:
   ```bash
   mkdir -p tools/marker
   ```

2. Create an isolated virtual environment using `uv` and install `marker-pdf`:
   ```bash
   # Create a virtual environment specifically for marker
   uv venv tools/marker/.venv
   
   # Install marker-pdf into that isolated environment
   # (Using VIRTUAL_ENV to ensure it targets the right venv)
   VIRTUAL_ENV=tools/marker/.venv uv pip install marker-pdf
   ```

## Running Scripts

Scripts should generally be run from the root of the repository using `uv run`, which ensures they have access to the main project's dependencies and source code.

### Example: `run_marker.py`

This script tests the integration with the `marker-pdf` CLI tool. Ensure you have set up the `marker-pdf` environment as described above before running it.

There are two main ways to run the script from the project root:

1. Running on a specific PDF using the `--pdf` argument:
   ```bash
   uv run scripts/run_marker.py --pdf data/some_file.pdf
   ```

2. Running on a set of targets using the `--targets` argument:
   ```bash
   uv run scripts/run_marker.py --targets scripts/targets.json
   ```
   This will parse the JSON file, extract the specific page ranges for each task, and run marker on each task individually, creating a separate output directory for each. The script produces both Markdown (`.md`) and JSON (`.json`) outputs for each target, providing both the extracted text and the detailed layout metadata.
