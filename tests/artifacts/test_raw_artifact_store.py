from __future__ import annotations

from pathlib import Path

import pytest

from doc_forge.artifacts import FilesystemArtifactStore
from doc_forge.corpus import SourceType


def test_raw_artifact_store_round_trips_markdown_bytes(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(tmp_path / "artifacts")

    ref = store.write_raw(
        workspace_id="ws-1",
        doc_id="doc-md",
        source_type=SourceType.MARKDOWN,
        content=b"# Heading\n\nParagraph.\n",
    )

    assert ref.relative_path == "raw/ws-1/doc-md/source.md"
    assert store.read_raw(ref) == b"# Heading\n\nParagraph.\n"


def test_raw_artifact_store_round_trips_pdf_bytes(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(tmp_path / "artifacts")

    ref = store.write_raw(
        workspace_id="ws-1",
        doc_id="doc-pdf",
        source_type=SourceType.PDF,
        content=b"%PDF-1.7\nfake",
    )

    assert ref.relative_path == "raw/ws-1/doc-pdf/source.pdf"
    assert store.read_raw(ref) == b"%PDF-1.7\nfake"


def test_raw_artifact_paths_are_deterministic_under_managed_root(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(tmp_path / "artifacts")

    path = store.raw_path(
        workspace_id="ws-1",
        doc_id="doc-md",
        source_type=SourceType.MARKDOWN,
    )

    assert path == tmp_path / "artifacts" / "raw" / "ws-1" / "doc-md" / "source.md"


def test_raw_artifact_store_rejects_unmanaged_relative_paths(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(tmp_path / "artifacts")

    with pytest.raises(ValueError, match="managed root"):
        store.resolve_relative_path("../escape.txt")


@pytest.mark.parametrize("workspace_id", [".", "..", "ws/unsafe", r"ws\unsafe", " ws-1", "ws-1 "])
def test_artifact_store_rejects_invalid_workspace_ids_before_path_construction(
    tmp_path: Path,
    workspace_id: str,
) -> None:
    store = FilesystemArtifactStore(tmp_path / "artifacts")

    with pytest.raises(ValueError, match="workspace_id"):
        store.raw_relative_path(
            workspace_id=workspace_id,
            doc_id="doc-md",
            source_type=SourceType.MARKDOWN,
        )

    with pytest.raises(ValueError, match="workspace_id"):
        store.extracted_relative_path(workspace_id=workspace_id, doc_id="doc-md")

    with pytest.raises(ValueError, match="workspace_id"):
        store.normalized_relative_path(workspace_id=workspace_id, doc_id="doc-md")


def test_raw_artifact_delete_is_idempotent(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(tmp_path / "artifacts")
    ref = store.write_raw(
        workspace_id="ws-1",
        doc_id="doc-md",
        source_type=SourceType.MARKDOWN,
        content=b"body",
    )

    store.delete_raw(ref)
    store.delete_raw(ref)

    assert not store.raw_path(
        workspace_id="ws-1",
        doc_id="doc-md",
        source_type=SourceType.MARKDOWN,
    ).exists()
