from __future__ import annotations

import pytest

from parity.cli import main


def test_cli_prints_ranked_results(capsys: pytest.CaptureFixture[str]) -> None:
    main()

    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()

    assert lines[0] == "Query: How does semantic retrieval help rag?"
    assert lines[1].startswith("1. score=")
    assert lines[2].startswith("2. score=")
