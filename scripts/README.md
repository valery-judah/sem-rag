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

### Example: `verify_marker.py`

This script tests the integration with the `marker-pdf` CLI tool. Ensure you have set up the `marker-pdf` environment as described above before running it.

To run the verification script from the project root:
```bash
uv run scripts/verify_marker.py
```
