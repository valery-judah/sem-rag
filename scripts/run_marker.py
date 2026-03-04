"""
Ad-hoc verification script for the Marker CLI engine.

For instructions on how to set up the required isolated environment for `marker-pdf`
and how to run this script, please see `scripts/README.md`.
"""

import argparse
import json
import sys
from pathlib import Path

from docforge.parsers.pdf_hybrid.engines.marker_cli import MarkerRunner


def run_marker_on_pdf(
    target_pdf: Path,
    runner: MarkerRunner,
    page_range: str | None = None,
    output_dir: Path | None = None,
):
    if output_dir is None:
        output_dir = Path("output/marker_test")

    # Ensure output dir exists
    output_dir.mkdir(parents=True, exist_ok=True)

    if not target_pdf.exists():
        print(f"Error: Target PDF not found at {target_pdf}")
        return

    range_str = f" (pages {page_range})" if page_range else ""
    print(f"\nRunning Marker on {target_pdf}{range_str}...")
    manifest = runner.run(
        target_pdf,
        output_dir,
        timeout_s=300,
        page_range=page_range,
        output_formats=["json", "markdown"],
    )

    print(f"Run completed with status: {manifest.status}")
    candidates = []
    if manifest.status != "ok":
        print(f"Error details: {manifest.error_details}")
        print(f"Stderr: {manifest.stderr}")
        # We don't return here so we can still check for generated Markdown files
    else:
        print(f"Loading and adapting output from {manifest.raw_output_dir}...")
        candidates = runner.load_and_adapt(manifest)
        print(f"Successfully adapted {len(candidates)} pages.")

    # Check for Markdown files alongside JSON files using the output_dir
    raw_dir = output_dir
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

    if manifest.status == "ok":
        # Print a few elements to verify
        for page in candidates[:2]:  # Just print the first 2 pages
            print(f"\n--- Page {page.page_idx} ---")
            for block in page.blocks[:3]:  # Print up to 3 blocks per page
                content = getattr(block, "text", str(block))[:100].replace("\n", " ")
                print(f"Block [{block.type}]: {content}...")


def main():
    parser = argparse.ArgumentParser(description="Run Marker CLI on PDF files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--pdf",
        type=str,
        help="Path to a specific PDF file to run on.",
    )
    group.add_argument(
        "--targets",
        type=str,
        help="Path to a JSON file containing targets.",
    )

    args = parser.parse_args()

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

    output_dir = Path("output/marker_test")
    # Ensure output dir exists
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.pdf:
        target_pdf = Path(args.pdf)
        run_marker_on_pdf(target_pdf, runner)
    elif args.targets:
        targets_file = Path(args.targets)
        if not targets_file.exists():
            print(f"Error: Targets file not found at {targets_file}")
            sys.exit(1)

        with open(targets_file) as f:
            targets_data = json.load(f)

        for target in targets_data:
            pdf_name = target.get("file")
            if not pdf_name:
                continue

            # Assume PDFs are in data/ directory
            target_pdf = Path("data") / pdf_name
            pdf_stem = target_pdf.stem

            for t in target.get("targets", []):
                if "pages" in t:
                    pages = t["pages"]
                    clean_page_range = pages.replace(",", "_").replace(" ", "")
                    output_dir = Path(f"output/marker_test/{pdf_stem}_{clean_page_range}")
                    run_marker_on_pdf(target_pdf, runner, page_range=pages, output_dir=output_dir)


if __name__ == "__main__":
    main()
