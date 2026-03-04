import json
import re
from pathlib import Path
import sys

def iter_blocks(node):
    """Recursively iterate through JSON AST blocks."""
    yield node
    for child in node.get("children", []) or []:
        yield from iter_blocks(child)

def verify_single_block(check, json_ast, md_content, output_dir):
    starts_with = check.get("starts_with")
    ends_with = check.get("ends_with")
    contains = check.get("contains")
    has_list = check.get("has_list")

    for block in iter_blocks(json_ast):
        text = block.get("html", "") or ""
        # The text may contain html tags like <p block-type="Text">...</p>
        # We can strip tags roughly or check inside them.
        stripped_text = re.sub(r'<[^>]+>', '', text).strip()
        
        match = True
        if starts_with and not stripped_text.startswith(starts_with):
            match = False
        if ends_with and not stripped_text.endswith(ends_with):
            match = False
        if contains and contains not in stripped_text:
            match = False
            
        if match and (starts_with or ends_with or contains):
            # Found a single block that satisfies the text criteria.
            # If we also need it to have a list, we should check its block_type or children
            if has_list:
                # Check if this block or its children contain a List
                has_list_child = any(c.get("block_type") == "List" for c in iter_blocks(block))
                if not has_list_child:
                    return False, "Found matching text, but it does not contain a List block."
            return True, None
            
    return False, "Could not find a single block satisfying the text criteria."

def verify_figure_linked(check, json_ast, md_content, output_dir):
    caption = check.get("caption", "")
    has_code = check.get("has_code")
    
    found_figure = False
    found_caption_match = False
    
    for block in iter_blocks(json_ast):
        if block.get("block_type") in ("FigureGroup", "Figure"):
            found_figure = True
            
            # Check caption
            block_html = block.get("html", "")
            # Also check children explicitly for Caption blocks
            caption_text = block_html
            for child in iter_blocks(block):
                if child.get("block_type") == "Caption":
                    caption_text += child.get("html", "")
                    
            if caption in caption_text:
                found_caption_match = True
                
                # Check for code if required
                if has_code:
                    has_code_child = any(c.get("block_type") in ("Code", "Preformatted") for c in iter_blocks(block))
                    if not has_code_child:
                        return False, f"Found Figure with caption '{caption}', but it does not contain code."
                
                # Check if an image is actually linked in the Markdown
                # Usually it looks like ![](_page_XX_Figure_Y.jpeg)
                image_links = re.findall(r'!\[.*?\]\((.*?)\)', md_content)
                if not image_links:
                    return False, "No image links found in Markdown."
                
                # We expect at least one image file from this figure group to exist on disk
                # Since we don't know the exact image name linked to this specific caption from MD easily,
                # we just verify that ANY linked image exists in the folder.
                for img_src in image_links:
                    img_path = output_dir / img_src
                    if img_path.exists():
                        return True, None
                
                return False, "Found image links in MD, but none of the files exist on disk."

    if not found_figure:
        return False, "No Figure/FigureGroup block found."
    if not found_caption_match:
        return False, f"Figure found, but caption '{caption}' not found."
        
    return False, "Unknown figure error."

def verify_table_linked(check, json_ast, md_content, output_dir):
    caption = check.get("caption", "")
    
    found_table = False
    for block in iter_blocks(json_ast):
        if block.get("block_type") == "Table":
            found_table = True
            block_html = block.get("html", "")
            # The table might have a caption child or be wrapped in a TableGroup
            if caption in block_html:
                # Check if MD contains table syntax (e.g., |...|...|)
                if "|" in md_content and "-|-" in md_content:
                    return True, None
                return False, "Found Table in JSON, but no markdown table syntax in MD."
    
    # Also check TableGroup
    for block in iter_blocks(json_ast):
        if block.get("block_type") == "TableGroup":
            found_table = True
            block_html = block.get("html", "")
            for child in iter_blocks(block):
                block_html += child.get("html", "")
            
            if caption in block_html:
                if "|" in md_content and "-|-" in md_content:
                    return True, None
                return False, "Found TableGroup in JSON, but no markdown table syntax in MD."

    if not found_table:
        return False, "No Table block found in JSON."
    return False, f"Table found, but caption '{caption}' not matched."

def verify_code_merged(check, json_ast, md_content, output_dir):
    contains = check.get("contains", "")
    
    for block in iter_blocks(json_ast):
        if block.get("block_type") in ("Code", "Preformatted", "CodeGroup"):
            # Check if this single code block contains the specified text
            block_html = block.get("html", "")
            stripped_text = re.sub(r'<[^>]+>', '', block_html)
            
            if contains in stripped_text:
                return True, None
                
    return False, f"Could not find a single Code block containing '{contains}'."

def verify_has_list(check, json_ast, md_content, output_dir):
    for block in iter_blocks(json_ast):
        if block.get("block_type") == "List":
            # Just verifying there is a list
            return True, None
            
    return False, "No List block found in JSON."

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

    print("Starting verification of parsed targets...\n")

    for target in targets_data:
        pdf_name = target.get("file")
        if not pdf_name:
            continue
            
        pdf_stem = Path(pdf_name).stem

        for t in target.get("targets", []):
            pages = t.get("pages", "")
            clean_page_range = pages.replace(",", "_").replace(" ", "")
            output_dir = Path(f"output/marker_test/{pdf_stem}_{clean_page_range}/{pdf_stem}")
            
            checks = t.get("checks", [])
            if not checks:
                continue
                
            json_path = output_dir / f"{pdf_stem}.json"
            md_path = output_dir / f"{pdf_stem}.md"
            
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

    if passed < total:
        sys.exit(1)

if __name__ == "__main__":
    main()
