from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI

from doc_forge.app.api import create_app
from doc_forge.app.deps import reset_runtime_caches


@pytest.fixture
def app(
    sql_engine,
    db_url: str,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[FastAPI]:
    del sql_engine
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("DOC_FORGE_ARTIFACT_ROOT", str(artifact_root))
    reset_runtime_caches()

    application = create_app()
    yield application

    reset_runtime_caches()
