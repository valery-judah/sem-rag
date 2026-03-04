"""
Ad-hoc verification script for the Marker CLI engine.

For instructions on how to set up the required isolated environment for `marker-pdf`
and how to run this script, please see `scripts/README.md`.
"""

import sys
from pathlib import Path

from docforge.parsers.pdf_hybrid.engines.marker_cli import MarkerRunner


def main():
    target_pdf = Path("data/llm-evals-course-notes-july.pdf")
    output_dir = Path("output/marker_test")

    if not target_pdf.exists():
        print(f"Error: Target PDF not found at {target_pdf}")
        sys.exit(1)

    print("Initializing MarkerRunner...")
    # On Apple Silicon, configure Marker to use MPS and a fixed amount of inference RAM
    env_overrides = {
        "TORCH_DEVICE": "mps",
        "INFERENCE_RAM": "24",  # or lower if needed
    }
    runner = MarkerRunner(env_overrides=env_overrides)

    bin_path = runner.discover()
    if not bin_path:
        print("Error: Marker binary not found. Is it installed in tools/marker/.venv?")
        sys.exit(1)

    print(f"Found Marker binary at: {bin_path}")
    version = runner.get_version()
    print(f"Marker version: {version}")

    # Ensure output dir exists
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Running Marker on {target_pdf}...")
    manifest = runner.run(target_pdf, output_dir, timeout_s=300)

    print(f"Run completed with status: {manifest.status}")
    if manifest.status != "ok":
        print(f"Error details: {manifest.error_details}")
        print(f"Stderr: {manifest.stderr}")
        sys.exit(1)

    print(f"Loading and adapting output from {manifest.raw_output_dir}...")
    candidates = runner.load_and_adapt(manifest)

    print(f"Successfully adapted {len(candidates)} pages.")

    # Check for Markdown files alongside JSON files
    raw_dir = Path(manifest.raw_output_dir)
    md_files = list(raw_dir.rglob("*.md"))
    json_files = list(raw_dir.rglob("*.json"))

    print(f"\nFound {len(json_files)} JSON files in {raw_dir}")
    for j in json_files:
        print(f"  - {j.name}")

    print(f"\nFound {len(md_files)} Markdown files in {raw_dir}")
    for m in md_files:
        print(f"  - {m.name}")

    if not md_files:
        print("\nWARNING: No Markdown files were generated!")
    elif not json_files:
        print("\nWARNING: No JSON files were generated!")
    else:
        print("\nSUCCESS: Both Markdown and JSON files were generated.")

    # Print a few elements to verify
    for page in candidates[:2]:  # Just print the first 2 pages
        print(f"\n--- Page {page.page_idx} ---")
        for block in page.blocks[:3]:  # Print up to 3 blocks per page
            content = getattr(block, "text", str(block))[:100].replace("\n", " ")
            print(f"Block [{block.type}]: {content}...")


if __name__ == "__main__":
    main()
