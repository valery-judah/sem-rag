"""Filesystem-backed storage for raw, extracted, and normalized artifacts."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from uuid import uuid4

from doc_forge.corpus import SourceType
from doc_forge.identifiers import DocId, WorkspaceId, parse_doc_id, parse_workspace_id

from .schemas import ExtractedArtifact, NormalizedArtifact, RawArtifactRef


class FilesystemArtifactStore:
    """Persist lifecycle artifacts under a managed root directory."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def raw_relative_path(
        self,
        *,
        workspace_id: WorkspaceId,
        doc_id: DocId,
        source_type: SourceType,
    ) -> str:
        workspace_id = parse_workspace_id(workspace_id)
        doc_id = parse_doc_id(doc_id)
        suffix = ".pdf" if source_type is SourceType.PDF else ".md"
        return str(PurePosixPath("raw") / workspace_id / doc_id / f"source{suffix}")

    def raw_path(
        self,
        *,
        workspace_id: WorkspaceId,
        doc_id: DocId,
        source_type: SourceType,
    ) -> Path:
        return self._resolve_relative_path(
            self.raw_relative_path(
                workspace_id=workspace_id,
                doc_id=doc_id,
                source_type=source_type,
            )
        )

    def extracted_relative_path(self, *, workspace_id: WorkspaceId, doc_id: DocId) -> str:
        workspace_id = parse_workspace_id(workspace_id)
        doc_id = parse_doc_id(doc_id)
        return str(PurePosixPath("extracted") / workspace_id / doc_id / "extracted.json")

    def extracted_path(self, *, workspace_id: WorkspaceId, doc_id: DocId) -> Path:
        return self._resolve_relative_path(
            self.extracted_relative_path(workspace_id=workspace_id, doc_id=doc_id)
        )

    def normalized_relative_path(self, *, workspace_id: WorkspaceId, doc_id: DocId) -> str:
        workspace_id = parse_workspace_id(workspace_id)
        doc_id = parse_doc_id(doc_id)
        return str(PurePosixPath("normalized") / workspace_id / doc_id / "normalized.json")

    def normalized_path(self, *, workspace_id: WorkspaceId, doc_id: DocId) -> Path:
        return self._resolve_relative_path(
            self.normalized_relative_path(workspace_id=workspace_id, doc_id=doc_id)
        )

    def write_raw(
        self,
        *,
        workspace_id: WorkspaceId,
        doc_id: DocId,
        source_type: SourceType,
        content: bytes,
    ) -> RawArtifactRef:
        relative_path = self.raw_relative_path(
            workspace_id=workspace_id,
            doc_id=doc_id,
            source_type=source_type,
        )
        path = self._resolve_relative_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return RawArtifactRef(
            workspace_id=workspace_id,
            doc_id=doc_id,
            source_type=source_type,
            relative_path=relative_path,
        )

    def read_raw(self, ref: RawArtifactRef) -> bytes:
        expected = self.raw_relative_path(
            workspace_id=ref.workspace_id,
            doc_id=ref.doc_id,
            source_type=ref.source_type,
        )
        if ref.relative_path != expected:
            raise ValueError("raw artifact reference does not match the managed path layout")
        return self._resolve_relative_path(ref.relative_path).read_bytes()

    def delete_raw(self, ref: RawArtifactRef) -> None:
        expected = self.raw_relative_path(
            workspace_id=ref.workspace_id,
            doc_id=ref.doc_id,
            source_type=ref.source_type,
        )
        if ref.relative_path != expected:
            raise ValueError("raw artifact reference does not match the managed path layout")
        self._unlink_if_exists(self._resolve_relative_path(ref.relative_path))

    def write_extracted(self, *, workspace_id: WorkspaceId, artifact: ExtractedArtifact) -> Path:
        path = self.extracted_path(workspace_id=workspace_id, doc_id=artifact.doc_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
        return path

    def read_extracted(self, *, workspace_id: WorkspaceId, doc_id: DocId) -> ExtractedArtifact:
        path = self.extracted_path(workspace_id=workspace_id, doc_id=doc_id)
        return ExtractedArtifact.model_validate_json(path.read_text(encoding="utf-8"))

    def delete_extracted(self, *, workspace_id: WorkspaceId, doc_id: DocId) -> None:
        self._unlink_if_exists(self.extracted_path(workspace_id=workspace_id, doc_id=doc_id))

    def write_normalized(
        self,
        *,
        workspace_id: WorkspaceId,
        artifact: NormalizedArtifact,
    ) -> Path:
        path = self.normalized_path(workspace_id=workspace_id, doc_id=artifact.doc_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
        return path

    def read_normalized(self, *, workspace_id: WorkspaceId, doc_id: DocId) -> NormalizedArtifact:
        path = self.normalized_path(workspace_id=workspace_id, doc_id=doc_id)
        return NormalizedArtifact.model_validate_json(path.read_text(encoding="utf-8"))

    def delete_normalized(self, *, workspace_id: WorkspaceId, doc_id: DocId) -> None:
        self._unlink_if_exists(self.normalized_path(workspace_id=workspace_id, doc_id=doc_id))

    def ensure_root_writable(self) -> None:
        """Create the managed root if needed and verify it is writable."""

        self._root.mkdir(parents=True, exist_ok=True)
        probe_path = self._root / f".doc_forge-write-probe-{uuid4().hex}"
        probe_path.write_text("", encoding="utf-8")
        probe_path.unlink()

    def _resolve_relative_path(self, relative_path: str) -> Path:
        relative = PurePosixPath(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("artifact paths must stay within the managed root")
        return self._root.joinpath(*relative.parts)

    def _unlink_if_exists(self, path: Path) -> None:
        if path.exists():
            path.unlink()
