from __future__ import annotations

from pathlib import Path

from parity.artifacts import FilesystemArtifactStore, NormalizedArtifact


def test_normalized_artifact_store_round_trips_fixture_snapshot(tmp_path: Path) -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "normalized" / "smoke.normalized.json"
    artifact = NormalizedArtifact.model_validate_json(fixture_path.read_text(encoding="utf-8"))
    store = FilesystemArtifactStore(tmp_path / "artifacts")

    store.write_normalized(workspace_id="ws-fixtures", artifact=artifact)
    loaded = store.read_normalized(workspace_id="ws-fixtures", doc_id=artifact.doc_id)

    assert loaded == artifact


def test_normalized_artifact_store_preserves_block_order(tmp_path: Path) -> None:
    artifact = NormalizedArtifact.model_validate_json(
        (
            Path(__file__).parent / "fixtures" / "normalized" / "design-exploration.normalized.json"
        ).read_text(encoding="utf-8")
    )
    store = FilesystemArtifactStore(tmp_path / "artifacts")

    store.write_normalized(workspace_id="ws-fixtures", artifact=artifact)
    loaded = store.read_normalized(workspace_id="ws-fixtures", doc_id=artifact.doc_id)

    assert [block.order_index for block in loaded.blocks] == list(range(len(loaded.blocks)))


def test_normalized_artifact_store_overwrites_document_path(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(tmp_path / "artifacts")
    first = NormalizedArtifact.model_validate_json(
        (Path(__file__).parent / "fixtures" / "normalized" / "smoke.normalized.json").read_text(
            encoding="utf-8"
        )
    )
    second = NormalizedArtifact.model_validate_json(
        (Path(__file__).parent / "fixtures" / "normalized" / "mvp.normalized.json").read_text(
            encoding="utf-8"
        )
    ).model_copy(update={"doc_id": first.doc_id})

    store.write_normalized(workspace_id="ws-fixtures", artifact=first)
    store.write_normalized(workspace_id="ws-fixtures", artifact=second)

    assert store.read_normalized(workspace_id="ws-fixtures", doc_id=first.doc_id) == second
