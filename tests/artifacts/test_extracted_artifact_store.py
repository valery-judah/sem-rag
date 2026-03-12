from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from doc_forge.artifacts import ExtractedArtifact, FilesystemArtifactStore


def test_extracted_artifact_store_round_trips_fixture_snapshot(tmp_path: Path) -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "extracted" / "smoke.extracted.json"
    artifact = ExtractedArtifact.model_validate_json(fixture_path.read_text(encoding="utf-8"))
    store = FilesystemArtifactStore(tmp_path / "artifacts")

    store.write_extracted(workspace_id="ws-fixtures", artifact=artifact)
    loaded = store.read_extracted(workspace_id="ws-fixtures", doc_id=artifact.doc_id)

    assert loaded == artifact


def test_extracted_artifact_store_rejects_invalid_schema_on_load(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(tmp_path / "artifacts")
    path = store.extracted_path(workspace_id="ws-fixtures", doc_id="doc-bad")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"doc_id": "doc-bad"}), encoding="utf-8")

    with pytest.raises(ValidationError):
        store.read_extracted(workspace_id="ws-fixtures", doc_id="doc-bad")


def test_extracted_artifact_store_overwrites_document_path(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(tmp_path / "artifacts")
    first = ExtractedArtifact.model_validate_json(
        (Path(__file__).parent / "fixtures" / "extracted" / "smoke.extracted.json").read_text(
            encoding="utf-8"
        )
    )
    second = ExtractedArtifact.model_validate_json(
        (Path(__file__).parent / "fixtures" / "extracted" / "mvp.extracted.json").read_text(
            encoding="utf-8"
        )
    ).model_copy(update={"doc_id": first.doc_id})

    store.write_extracted(workspace_id="ws-fixtures", artifact=first)
    store.write_extracted(workspace_id="ws-fixtures", artifact=second)

    assert store.read_extracted(workspace_id="ws-fixtures", doc_id=first.doc_id) == second
