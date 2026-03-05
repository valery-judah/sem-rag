"""
Ad-hoc verification script for the MinerU CLI engine.
"""

import argparse
import json
import sys
from pathlib import Path

from docforge.parsers.pdf_hybrid.engines.mineru_cli import MineruRunner


def run_mineru_on_pdf(
    target_pdf: Path,
    runner: MineruRunner,
    start_page: int | None = None,
    end_page: int | None = None,
    output_dir: Path | None = None,
):
    if output_dir is None:
        output_dir = Path("output/mineru_test")

    output_dir.mkdir(parents=True, exist_ok=True)

    if not target_pdf.exists():
        print(f"Error: Target PDF not found at {target_pdf}")
        return

    range_str = f" (pages {start_page}-{end_page})" if start_page is not None else ""
    print(f"\nRunning MinerU on {target_pdf}{range_str}...")
    manifest = runner.run(
        target_pdf,
        output_dir,
        timeout_s=300,
        start_page=start_page,
        end_page=end_page,
    )

    print(f"Run completed with status: {manifest.status}")
    candidates = []
    if manifest.status != "ok":
        print(f"Error details: {manifest.error_details}")
        print(f"Stderr: {manifest.stderr}")
    else:
        print(f"Loading and adapting output from {manifest.raw_output_dir}...")
        candidates = runner.load_and_adapt(manifest)
        print(f"Successfully adapted {len(candidates)} pages.")

        # Write out the adapted .json and .md files
        if candidates:
            adapted_json = output_dir / "adapted.json"
            adapted_md = output_dir / "adapted.md"

            with open(adapted_json, "w", encoding="utf-8") as f:
                json.dump([c.model_dump() for c in candidates], f, indent=2)

            with open(adapted_md, "w", encoding="utf-8") as f:
                for c in candidates:
                    for b in c.blocks:
                        content = getattr(b, "text", str(b))
                        f.write(content + "\n\n")

            print(f"Wrote adapted output to {adapted_json.name} and {adapted_md.name}")

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
        for page in candidates[:2]:
            print(f"\n--- Page {page.page_idx} ---")
            for block in page.blocks[:3]:
                content = getattr(block, "text", str(block))[:100].replace("\n", " ")
                print(f"Block [{block.type}]: {content}...")


def parse_page_range(pages_str: str) -> tuple[int, int]:
    """Converts 1-based human page ranges to 0-based runner limits."""
    if "," in pages_str:
        raise ValueError(f"Comma-separated page ranges are not supported: {pages_str}")

    if "-" in pages_str:
        parts = pages_str.split("-")
        start = int(parts[0]) - 1
        end = int(parts[1]) - 1
        return start, end

    val = int(pages_str) - 1
    return val, val


def main():
    parser = argparse.ArgumentParser(description="Run MinerU CLI on PDF files.")
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

    print("Initializing MineruRunner...")
    runner = MineruRunner()

    bin_path = runner.discover()
    if not bin_path:
        print("Error: MinerU binary not found. Is it installed in tools/mineru/.venv?")
        sys.exit(1)

    print(f"Found MinerU binary at: {bin_path}")
    version = runner.get_version()
    print(f"MinerU version: {version}")

    output_dir = Path("output/mineru_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.pdf:
        target_pdf = Path(args.pdf)
        run_mineru_on_pdf(target_pdf, runner)
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

            target_pdf = Path("data") / pdf_name
            pdf_stem = target_pdf.stem

            for t in target.get("targets", []):
                if "pages" in t:
                    pages = t["pages"]
                    clean_page_range = pages.replace(",", "_").replace(" ", "")
                    output_dir = Path(f"output/mineru_test/{pdf_stem}_{clean_page_range}")

                    try:
                        start_page, end_page = parse_page_range(pages)
                    except ValueError as e:
                        print(f"Error parsing page range: {e}")
                        continue

                    run_mineru_on_pdf(
                        target_pdf,
                        runner,
                        start_page=start_page,
                        end_page=end_page,
                        output_dir=output_dir,
                    )


if __name__ == "__main__":
    main()
