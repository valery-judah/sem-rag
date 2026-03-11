from pathlib import Path


def main():
    target_dirs = ["src", "tests"]

    total_py_files = 0
    total_lines = 0

    domain_py_files = 0
    domain_lines = 0

    total_line_length = 0

    for d in target_dirs:
        p = Path(d)
        if not p.exists():
            continue

        for filepath in p.rglob("*.py"):
            total_py_files += 1

            with open(filepath, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            num_lines = len(lines)
            total_lines += num_lines
            total_line_length += sum(len(line.strip("\n")) for line in lines)

            if filepath.name != "__init__.py":
                domain_py_files += 1
                domain_lines += num_lines

    avg_lines_per_domain_file = domain_lines / domain_py_files if domain_py_files > 0 else 0
    avg_line_length = total_line_length / total_lines if total_lines > 0 else 0

    print(f"Total .py files: {total_py_files}")
    print(f"Total lines: {total_lines}")
    print(f"Average lines per domain-specific file: {avg_lines_per_domain_file:.2f}")
    print(f"Average line length: {avg_line_length:.2f}")


if __name__ == "__main__":
    main()
