from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
    from doc_forge.devtools.dead_code import main as dead_code_main

    return dead_code_main()


if __name__ == "__main__":
    raise SystemExit(main())
