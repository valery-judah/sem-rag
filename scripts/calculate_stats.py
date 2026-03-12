from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass
class Stats:
    total_py_files: int = 0
    total_lines: int = 0
    domain_py_files: int = 0
    domain_lines: int = 0

    def add(self, other: "Stats"):
        self.total_py_files += other.total_py_files
        self.total_lines += other.total_lines
        self.domain_py_files += other.domain_py_files
        self.domain_lines += other.domain_lines

    @property
    def avg_lines_per_domain_file(self) -> float:
        return self.domain_lines / self.domain_py_files if self.domain_py_files > 0 else 0.0


def print_row(name: str, stats: Stats, indent: int = 0):
    folder_col = (" " * indent + name).ljust(40)
    files_col = str(stats.total_py_files).rjust(15)
    lines_col = str(stats.total_lines).rjust(15)
    avg_col = f"{stats.avg_lines_per_domain_file:.2f}".rjust(27)
    print(f"{folder_col} | {files_col} | {lines_col} | {avg_col}")


def main():
    target_dirs = ["src", "tests"]

    dir_stats: Dict[Path, Stats] = defaultdict(Stats)
    overall_stats = Stats()

    for d in target_dirs:
        p = Path(d)
        if not p.exists():
            continue

        for filepath in p.rglob("*.py"):
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            num_lines = len(lines)
            is_domain = filepath.name != "__init__.py"

            file_stats = Stats(
                total_py_files=1,
                total_lines=num_lines,
                domain_py_files=1 if is_domain else 0,
                domain_lines=num_lines if is_domain else 0,
            )

            overall_stats.add(file_stats)

            current_dir = filepath.parent
            while True:
                dir_stats[current_dir].add(file_stats)
                if current_dir == p or current_dir == Path("."):
                    break
                current_dir = current_dir.parent

    # Print header
    header_folder = "Folder".ljust(40)
    header_files = "Total .py Files".rjust(15)
    header_lines = "Total Lines".rjust(15)
    header_avg = "Avg Lines per Domain File".rjust(27)
    header = f"{header_folder} | {header_files} | {header_lines} | {header_avg}"
    print(header)
    print("-" * len(header))

    print_row("Overall (src + tests)", overall_stats)
    print("-" * len(header))

    for d in target_dirs:
        p = Path(d)
        if p in dir_stats:
            print_row(str(p), dir_stats[p], indent=0)

            subdirs = [subdir for subdir in dir_stats.keys() if subdir.is_relative_to(p) and subdir != p]
            subdirs.sort()

            for subdir in subdirs:
                # Limit the depth of printed subdirectories
                depth = len(subdir.parts)
                if depth <= 3:
                    print_row(str(subdir), dir_stats[subdir], indent=2 * (depth - 1))


if __name__ == "__main__":
    main()
