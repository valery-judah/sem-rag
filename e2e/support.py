"""System Driver DSL for E2E tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from pydantic import BaseModel, ConfigDict


class UploadReceipt(BaseModel):
    model_config = ConfigDict(extra="ignore")

    doc_id: str
    ingest_status: str
    source_type: str
    filename: str
    title: str
    checksum: str


class DocumentStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")

    doc_id: str
    ingest_status: str
    source_type: str
    title: str
    filename: str
    failure_code: str | None = None
    failure_detail: str | None = None
    active_job_stage: str | None = None

    @property
    def is_ready(self) -> bool:
        return self.ingest_status.lower() == "ready"

    @property
    def is_failed(self) -> bool:
        return self.ingest_status.lower() == "failed"


class ArtifactRefs(BaseModel):
    model_config = ConfigDict(extra="ignore")

    doc_id: str
    raw_path: str | None = None
    extracted_path: str | None = None
    normalized_path: str | None = None


class SearchHit(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chunk_id: str
    doc_id: str
    score: float


class QueryResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    doc_id: str
    hits: list[SearchHit]

    @property
    def top_hit(self) -> SearchHit | None:
        if not self.hits:
            return None
        return self.hits[0]


@dataclass(frozen=True)
class E2EReadyDocument:
    doc_id: str
    artifacts: ArtifactRefs

    def _host_artifact_path(self, e2e_stack, artifact_path: str | None):
        host_path = e2e_stack.host_artifact_path(artifact_path)
        assert host_path is not None
        return host_path

    def assert_artifacts_exist(self, e2e_stack) -> None:
        """INVARIANT: Artifact Integrity - files exist physically on the host."""
        assert self._host_artifact_path(e2e_stack, self.artifacts.raw_path).exists()
        assert self._host_artifact_path(e2e_stack, self.artifacts.extracted_path).exists()
        assert self._host_artifact_path(e2e_stack, self.artifacts.normalized_path).exists()

    def assert_artifacts_deleted(self, e2e_stack) -> None:
        """INVARIANT: Garbage Collection - files are removed from the host."""
        assert not self._host_artifact_path(e2e_stack, self.artifacts.raw_path).exists()
        assert not self._host_artifact_path(e2e_stack, self.artifacts.extracted_path).exists()
        assert not self._host_artifact_path(e2e_stack, self.artifacts.normalized_path).exists()

    def assert_strict_vector_mapping(self, e2e_stack) -> None:
        """INVARIANT: Strict 1:1:1 mapping of chunks, embeddings, and index entries."""
        snapshot = e2e_stack.vector_snapshot(doc_id=self.doc_id)

        chunk_count = cast(int, snapshot["chunk_count"])
        embedding_count = cast(int, snapshot["embedding_count"])
        index_entry_count = cast(int, snapshot["index_entry_count"])

        assert chunk_count > 0
        assert embedding_count > 0
        assert index_entry_count > 0
        assert embedding_count == chunk_count
        assert index_entry_count == chunk_count

        sample_embedding = snapshot["sample_embedding"]
        assert sample_embedding is not None
        assert sample_embedding["embedding_model"]
        assert isinstance(sample_embedding["embedding_vector_json"], list)
        assert sample_embedding["embedding_vector_json"]

    def assert_vectors_deleted(self, e2e_stack) -> None:
        """INVARIANT: Garbage Collection - vectors and chunks are deleted."""
        snapshot = e2e_stack.vector_snapshot(doc_id=self.doc_id)
        assert snapshot["chunk_count"] == 0
        assert snapshot["embedding_count"] == 0
        assert snapshot["index_entry_count"] == 0


class SystemDriver:
    """Encapsulates system interactions behind a clean semantic DSL."""

    def __init__(self, e2e_stack):
        self.stack = e2e_stack

    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def _submit(
        self,
        *,
        file_name: str,
        file_content: bytes,
        content_type: str,
        title: str,
        workspace_id: str,
    ) -> UploadReceipt:
        with self.stack.client() as client:
            upload = client.post(
                "/documents",
                data={"workspace_id": workspace_id, "title": title},
                files={"file": (file_name, file_content, content_type)},
            )
            upload.raise_for_status()
            receipt = UploadReceipt.model_validate(upload.json())
            self.stack.log("document upload accepted", doc_id=receipt.doc_id, title=title)
            return receipt

    def submit_document(
        self,
        *,
        path: Path | str,
        title: str,
        workspace_id: str = "ws-docs",
    ) -> UploadReceipt:
        absolute_path = self._repo_root() / Path(path)
        self.stack.log("uploading repo document", path=str(absolute_path), title=title)
        with absolute_path.open("rb") as handle:
            return self._submit(
                file_name=absolute_path.name,
                file_content=handle.read(),
                content_type="text/markdown",
                title=title,
                workspace_id=workspace_id,
            )

    def submit_markdown_bytes(
        self,
        *,
        filename: str,
        title: str,
        content: bytes,
        workspace_id: str = "ws-docs",
    ) -> UploadReceipt:
        self.stack.log("uploading synthetic markdown document", filename=filename, title=title)
        return self._submit(
            file_name=filename,
            file_content=content,
            content_type="text/markdown",
            title=title,
            workspace_id=workspace_id,
        )

    def wait_for_terminal_status(
        self,
        doc_id: str,
        *,
        timeout_seconds: float = 90.0,
    ) -> DocumentStatus:
        with self.stack.client() as client:
            status = self.stack.wait_for_document(
                client,
                doc_id=doc_id,
                timeout_seconds=timeout_seconds,
            )
        return DocumentStatus.model_validate(status)

    def get_document_status(self, doc_id: str) -> DocumentStatus:
        with self.stack.client() as client:
            response = client.get(f"/documents/{doc_id}/status")
            response.raise_for_status()
            return DocumentStatus.model_validate(response.json())

    def get_artifacts(self, doc_id: str) -> ArtifactRefs:
        with self.stack.client() as client:
            artifacts = client.get(f"/documents/{doc_id}/artifacts")
            artifacts.raise_for_status()
            return ArtifactRefs.model_validate(artifacts.json())

    def wait_for_ready_document(
        self,
        doc_id: str,
        *,
        timeout_seconds: float = 90.0,
    ) -> E2EReadyDocument:
        status = self.wait_for_terminal_status(doc_id, timeout_seconds=timeout_seconds)
        assert status.is_ready
        return E2EReadyDocument(doc_id=doc_id, artifacts=self.get_artifacts(doc_id))

    def ingest_document(
        self,
        *,
        path: Path | str,
        title: str,
        workspace_id: str = "ws-docs",
        timeout_seconds: float = 90.0,
    ) -> E2EReadyDocument:
        receipt = self.submit_document(path=path, title=title, workspace_id=workspace_id)
        return self.wait_for_ready_document(receipt.doc_id, timeout_seconds=timeout_seconds)

    def ingest_markdown_bytes(
        self,
        *,
        filename: str,
        title: str,
        content: bytes,
        workspace_id: str = "ws-docs",
        timeout_seconds: float = 90.0,
    ) -> E2EReadyDocument:
        receipt = self.submit_markdown_bytes(
            filename=filename,
            title=title,
            content=content,
            workspace_id=workspace_id,
        )
        return self.wait_for_ready_document(receipt.doc_id, timeout_seconds=timeout_seconds)

    def query(self, doc_id: str, text: str, k: int = 1) -> QueryResult:
        with self.stack.client() as client:
            query_response = client.post(
                "/retrieval/query",
                json={"doc_id": doc_id, "query": text, "k": k},
            )
            query_response.raise_for_status()
            self.stack.log("retrieval query completed", doc_id=doc_id, query=text, k=k)
            return QueryResult.model_validate(query_response.json())

    def delete_document(self, doc_id: str) -> None:
        with self.stack.client() as client:
            delete_resp = client.delete(f"/documents/{doc_id}")
            delete_resp.raise_for_status()
            self.stack.log("document deleted", doc_id=doc_id)
