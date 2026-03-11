from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.pipeline


def test_fixture_markdown_files_exist(fixture_dir):
    assert (fixture_dir / "simple.md").exists()
    assert (fixture_dir / "handbook.md").exists()
