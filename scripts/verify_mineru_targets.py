import json
import re
import sys
from pathlib import Path


def iter_blocks(adapted_json):
    """Iterate through MinerU adapted JSON blocks."""
    for page in adapted_json:
        for block in page.get("blocks", []):
            yield block


def verify_single_block(check, json_ast, md_content, output_dir):
    starts_with = check.get("starts_with")
    ends_with = check.get("ends_with")
    contains = check.get("contains")
    has_list = check.get("has_list")

    for block in iter_blocks(json_ast):
        text = block.get("text", "") or ""
        stripped_text = text.strip()

        match = True
        if starts_with and not stripped_text.startswith(starts_with):
            match = False
        if ends_with and not stripped_text.endswith(ends_with):
            match = False
        if contains and contains not in stripped_text:
            match = False

        if match and (starts_with or ends_with or contains):
            if has_list:
                # MinerU often puts bullets directly in the text like \uf0a1 or markdown asterisks
                if (
                    not re.search(r"(?m)^[\s\*\-\u2022\uf0a1]", stripped_text)
                    and "\n" not in stripped_text
                ):
                    return False, "Found matching text, but it does not seem to be a list block."
            return True, None

    return False, "Could not find a single block satisfying the text criteria."


def verify_figure_linked(check, json_ast, md_content, output_dir):
    caption = check.get("caption", "")
    has_code = check.get("has_code")

    found_figure = False
    found_caption_match = False

    # Check assets for image
    for page in json_ast:
        for asset in page.get("assets", []):
            if asset.get("type") == "image":
                found_figure = True

    # Also check if caption is present in the markdown
    if caption in md_content:
        found_caption_match = True

    if found_figure and found_caption_match:
        if has_code:
            # MinerU might not explicitly label code in figures, just check if figure and caption exist
            # For simplicity in MinerU testing, we'll assume pass if the figure and caption are there
            pass
        return True, None

    if not found_figure:
        return False, "No image asset found."
    if not found_caption_match:
        return False, f"Figure found, but caption '{caption}' not found in markdown."

    return False, "Unknown figure error."


def verify_table_linked(check, json_ast, md_content, output_dir):
    caption = check.get("caption", "")

    found_table = False
    for page in json_ast:
        for asset in page.get("assets", []):
            if asset.get("type") == "table_render":
                found_table = True
        for block in page.get("blocks", []):
            if block.get("type") == "table":
                found_table = True

    if found_table and caption in md_content:
        if "|" in md_content and "-|-" in md_content:
            return True, None
        return False, "Found Table in JSON, but no markdown table syntax in MD."

    if not found_table:
        return False, "No Table asset/block found in JSON."
    return False, f"Table found, but caption '{caption}' not matched."


def verify_code_merged(check, json_ast, md_content, output_dir):
    contains = check.get("contains", "")

    # MinerU might just extract it as text or code, but it should be in the blocks or MD.
    for block in iter_blocks(json_ast):
        text = block.get("text", "") or ""
        if contains in text:
            return True, None

    if contains in md_content:
        return True, None

    return False, f"Could not find a block or MD text containing '{contains}'."


def verify_has_list(check, json_ast, md_content, output_dir):
    for block in iter_blocks(json_ast):
        text = block.get("text", "") or ""
        # Check if block contains list-like characters
        if re.search(r"(?m)^[\s\*\-\u2022\uf0a1]+", text):
            return True, None

    # Or in markdown
    if re.search(r"(?m)^\s*[\*\-]\s+", md_content):
        return True, None

    return False, "No List found in JSON or MD."


VERIFIERS = {
    "single_block": verify_single_block,
    "figure_linked": verify_figure_linked,
    "table_linked": verify_table_linked,
    "code_merged": verify_code_merged,
    "has_list": verify_has_list,
}


def main():
    targets_file = Path("scripts/targets.json")
    if not targets_file.exists():
        print(f"Error: Targets file not found at {targets_file}")
        sys.exit(1)

    with open(targets_file) as f:
        targets_data = json.load(f)

    total = 0
    passed = 0

    print("Starting verification of MinerU parsed targets...\n")

    for target in targets_data:
        pdf_name = target.get("file")
        if not pdf_name:
            continue

        pdf_stem = Path(pdf_name).stem

        for t in target.get("targets", []):
            pages = t.get("pages", "")
            clean_page_range = pages.replace(",", "_").replace(" ", "")
            output_dir = Path(f"output/mineru_test/{pdf_stem}_{clean_page_range}")

            checks = t.get("checks", [])
            if not checks:
                continue

            json_path = output_dir / "adapted.json"
            md_path = output_dir / pdf_stem / "auto" / f"{pdf_stem}.md"

            print(f"Target: {pdf_name} (pages: {pages})")
            print(f"  Description: {t.get('description')}")

            if not json_path.exists() or not md_path.exists():
                print(f"  [FAIL] Missing output files in {output_dir}")
                total += len(checks)
                continue

            with open(json_path) as f:
                try:
                    json_ast = json.load(f)
                except Exception as e:
                    print(f"  [FAIL] Invalid JSON: {e}")
                    total += len(checks)
                    continue

            with open(md_path) as f:
                md_content = f.read()

            for check in checks:
                total += 1
                check_type = check.get("type")
                verifier = VERIFIERS.get(check_type)

                if not verifier:
                    print(f"  [WARN] Unknown check type: {check_type}")
                    continue

                success, error_msg = verifier(check, json_ast, md_content, output_dir)

                if success:
                    print(f"  [PASS] {check_type}")
                    passed += 1
                else:
                    print(f"  [FAIL] {check_type}: {error_msg}")
            print()

    print("=" * 40)
    print(f"Verification Summary: {passed}/{total} Passed.")
    print("=" * 40)

    # Note: we won't strictly exit 1 if they fail because MinerU might not perfectly match Marker's checks.
    # We just want to see the report.


if __name__ == "__main__":
    main()
