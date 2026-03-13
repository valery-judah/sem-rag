from pathlib import Path

SETS_ROOT = Path("evals/cases/sets")
CANONICAL_NAMES = {
    "cases": "cases.jsonl",
    "answer_keys": "answer_keys.jsonl",
}


def main() -> None:
    renamed = 0
    skipped = 0

    for set_dir in sorted(path for path in SETS_ROOT.iterdir() if path.is_dir()):
        jsonl_files = [path for path in set_dir.iterdir() if path.suffix == ".jsonl"]
        by_name = {path.name for path in jsonl_files}

        for key, target_name in CANONICAL_NAMES.items():
            target_path = set_dir / target_name

            if target_name in by_name:
                continue

            matches = [
                path for path in jsonl_files if key in path.stem and path.name != target_name
            ]

            if not matches:
                continue

            if len(matches) > 1:
                print(f"skip conflict: {set_dir}")
                skipped += 1
                continue

            source_path = matches[0]
            if target_path.exists():
                print(f"skip existing: {target_path}")
                skipped += 1
                continue

            source_path.rename(target_path)
            print(f"{source_path} -> {target_path}")
            renamed += 1

    print(f"renamed={renamed} skipped={skipped}")


if __name__ == "__main__":
    main()
