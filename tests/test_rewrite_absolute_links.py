from __future__ import annotations

import runpy
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rewrite_absolute_links.py"
SCRIPT_GLOBALS = runpy.run_path(str(SCRIPT_PATH))
relativize_target = SCRIPT_GLOBALS["relativize_target"]
rewrite_text = SCRIPT_GLOBALS["rewrite_text"]


def test_relativize_target_uses_source_file_directory() -> None:
    source_file = Path(
        "/Users/val/projects/rag/sem-rag/docs/workstreams/WS-006-query-lifecycle/example.md"
    )

    relative_target = relativize_target(
        source_file,
        "/Users/val/projects/rag/sem-rag/src/parity/query/contracts.py",
    )

    assert relative_target == "../../../src/parity/query/contracts.py"


def test_rewrite_text_preserves_suffixes() -> None:
    source_file = Path("/Users/val/projects/rag/sem-rag/docs/evergreen/architecture.md")
    content = (
        "[api](https://example.com) "
        "[query](//not-a-match) "
        "[contracts](/Users/val/projects/rag/sem-rag/src/parity/query/contracts.py#L10)"
    )

    rewritten, replacements = rewrite_text(source_file, content)

    assert (
        rewritten
        == "[api](https://example.com) "
        "[query](//not-a-match) "
        "[contracts](../../src/parity/query/contracts.py#L10)"
    )
    assert len(replacements) == 1
