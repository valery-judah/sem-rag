from __future__ import annotations

import hashlib
import io
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .builders import (
    FIXED_NOW,
    new_chunk,
    new_document,
    new_extracted_artifact,
    new_index_entry,
    new_normalized_block,
    new_normalized_payload,
    new_section,
)


@dataclass
class UploadContext:
    upload_id: str
    workspace_id: str
    filename: str
    title: str
    source_type: str
    checksum: str
    raw_storage_path: str
    size_bytes: int


class FakeArtifactStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir
        self.raw: dict[str, bytes] = {}
        self.objects: dict[str, Any] = {}
        self.events: list[tuple[str, str]] = []

    def write_raw(self, *, path: str, data: bytes) -> str:
        self.raw[path] = data
        self.events.append(("write_raw", path))
        if self.base_dir:
            full = self.base_dir / path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_bytes(data)
        return path

    def read_raw(self, *, path: str) -> bytes:
        if path in self.raw:
            return self.raw[path]
        if self.base_dir:
            return (self.base_dir / path).read_bytes()
        raise KeyError(path)

    def write_json(self, *, path: str, payload: Any) -> str:
        self.objects[path] = payload
        self.events.append(("write_json", path))
        if self.base_dir:
            full = self.base_dir / path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(json.dumps(payload, default=str), encoding="utf-8")
        return path

    def read_json(self, *, path: str) -> Any:
        if path in self.objects:
            return self.objects[path]
        if self.base_dir:
            return json.loads((self.base_dir / path).read_text(encoding="utf-8"))
        raise KeyError(path)

    def exists(self, *, path: str) -> bool:
        if path in self.raw or path in self.objects:
            return True
        return bool(self.base_dir and (self.base_dir / path).exists())

    def list_written_paths(self) -> list[str]:
        return [path for _, path in self.events]


class FakeDocumentRepository:
    def __init__(self) -> None:
        self.docs: dict[str, Any] = {}
        self.status_updates: list[dict[str, Any]] = []

    def create(self, document: Any) -> None:
        doc_id = getattr(document, "doc_id")
        if doc_id in self.docs:
            raise ValueError(f"duplicate document: {doc_id}")
        self.docs[doc_id] = document

    def get(self, doc_id: str) -> Any:
        return self.docs[doc_id]

    def list(self) -> list[Any]:
        return list(self.docs.values())

    def update_status(self, doc_id: str, status: Any, **kwargs: Any) -> None:
        doc = self.docs[doc_id]
        if hasattr(doc, "status"):
            setattr(doc, "status", status)
        if hasattr(doc, "ingest_status"):
            setattr(doc, "ingest_status", status)
        for key, value in kwargs.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        self.status_updates.append({"doc_id": doc_id, "status": status, **kwargs})

    def exists(self, doc_id: str) -> bool:
        return doc_id in self.docs


class FakeLifecycleEventRepository:
    def __init__(self) -> None:
        self.events: list[Any] = []

    def append(self, event: Any) -> None:
        self.events.append(event)

    def list_for_document(self, doc_id: str) -> list[Any]:
        return [event for event in self.events if getattr(event, "doc_id", None) == doc_id]


class FakeSectionRepository:
    def __init__(self) -> None:
        self.sections_by_doc: dict[str, list[Any]] = defaultdict(list)
        self.replace_calls: list[str] = []

    def replace_for_document(self, doc_id: str, sections: list[Any]) -> None:
        self.sections_by_doc[doc_id] = list(sections)
        self.replace_calls.append(doc_id)

    def list_for_document(self, doc_id: str) -> list[Any]:
        return list(self.sections_by_doc.get(doc_id, []))


class FakeChunkRepository:
    def __init__(self) -> None:
        self.chunks_by_doc: dict[str, list[Any]] = defaultdict(list)
        self.replace_calls: list[str] = []

    def replace_for_document(self, doc_id: str, chunks: list[Any]) -> None:
        self.chunks_by_doc[doc_id] = list(chunks)
        self.replace_calls.append(doc_id)

    def list_for_document(self, doc_id: str) -> list[Any]:
        return list(self.chunks_by_doc.get(doc_id, []))


class FakeIndexEntryRepository:
    def __init__(self) -> None:
        self.entries_by_doc: dict[str, list[Any]] = defaultdict(list)
        self.replace_calls: list[str] = []
        self.delete_calls: list[str] = []

    def replace_for_document(self, doc_id: str, entries: list[Any]) -> None:
        self.entries_by_doc[doc_id] = list(entries)
        self.replace_calls.append(doc_id)

    def delete_for_document(self, doc_id: str) -> None:
        self.entries_by_doc[doc_id] = []
        self.delete_calls.append(doc_id)

    def list_for_document(self, doc_id: str) -> list[Any]:
        return list(self.entries_by_doc.get(doc_id, []))


class FakeJobsRepository:
    def __init__(self) -> None:
        self.enqueued: list[dict[str, Any]] = []
        self.claimed: list[str] = []
        self.status_by_job_id: dict[str, str] = {}

    def enqueue(self, *, doc_id: str, target_stage: str, **kwargs: Any) -> str:
        job_id = kwargs.get("job_id", f"job_{len(self.enqueued) + 1}")
        self.enqueued.append({"job_id": job_id, "doc_id": doc_id, "target_stage": target_stage, **kwargs})
        self.status_by_job_id[job_id] = "queued"
        return job_id

    def mark_succeeded(self, job_id: str) -> None:
        self.status_by_job_id[job_id] = "succeeded"

    def reschedule(self, job_id: str, **kwargs: Any) -> None:
        self.status_by_job_id[job_id] = "queued"
        self.enqueued.append({"job_id": job_id, **kwargs})

    def list_for_document(self, doc_id: str) -> list[dict[str, Any]]:
        return [job for job in self.enqueued if job["doc_id"] == doc_id]


class FakeVectorIndex:
    def __init__(self) -> None:
        self.index: dict[str, dict[str, Any]] = {}
        self.upserts: list[dict[str, Any]] = []
        self.deletes: list[str] = []

    def upsert_chunk(self, *, chunk_id: str, text: str, metadata: dict) -> str:
        index_key = f"pgvector:{chunk_id}"
        self.index[chunk_id] = {
            "index_key": index_key,
            "text": text,
            "metadata": metadata,
        }
        self.upserts.append({"chunk_id": chunk_id, "text": text, "metadata": metadata})
        return index_key

    def delete_chunks_for_document(self, *, doc_id: str) -> None:
        doomed = [chunk_id for chunk_id, row in self.index.items() if row["metadata"].get("doc_id") == doc_id]
        for chunk_id in doomed:
            del self.index[chunk_id]
        self.deletes.append(doc_id)

    def smoke_query(self, *, doc_id: str, text: str, k: int = 1) -> list[dict]:
        rows = []
        for chunk_id, row in self.index.items():
            if row["metadata"].get("doc_id") != doc_id:
                continue
            haystack = row["text"].lower()
            needle = text.lower()
            if needle in haystack or any(token and token in haystack for token in needle.split()):
                rows.append({"chunk_id": chunk_id, "doc_id": doc_id, "score": 1.0})
        return rows[:k]


class FakeExtractionService:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.raise_error: Exception | None = None

    def extract(self, *, doc: Any) -> Any:
        self.calls.append(getattr(doc, "doc_id"))
        if self.raise_error:
            raise self.raise_error
        source_type = getattr(doc, "source_type", "markdown")
        if str(source_type).lower().endswith("pdf") or str(source_type).lower() == "pdf":
            return new_extracted_artifact(
                doc_id=getattr(doc, "doc_id"),
                source_type="pdf",
                meta={"warnings": []},
                payload_path=f"data/extracted/{getattr(doc, 'doc_id')}/extracted.json",
            )
        return new_extracted_artifact(
            doc_id=getattr(doc, "doc_id"),
            source_type="markdown",
            meta={"warnings": []},
            payload_path=f"data/extracted/{getattr(doc, 'doc_id')}/extracted.json",
        )


class FakeNormalizationService:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.raise_error: Exception | None = None

    def normalize(self, *, doc: Any, extracted: Any) -> Any:
        self.calls.append(getattr(doc, "doc_id"))
        if self.raise_error:
            raise self.raise_error
        source_type = getattr(extracted, "source_type", "markdown")
        if source_type == "pdf":
            blocks = [
                new_normalized_block(
                    block_id="blk_1",
                    kind="page_break",
                    text="Page 1",
                    order_index=0,
                    page_start=1,
                    page_end=1,
                    meta={},
                ),
                new_normalized_block(
                    block_id="blk_2",
                    kind="heading",
                    text="1 Introduction",
                    order_index=1,
                    heading_level=1,
                    page_start=1,
                    page_end=1,
                    meta={"inferred": True},
                ),
                new_normalized_block(
                    block_id="blk_3",
                    kind="paragraph",
                    text="Document lifecycle preserves persisted evidence.",
                    order_index=2,
                    page_start=1,
                    page_end=1,
                    meta={},
                ),
            ]
            return new_normalized_payload(doc_id=getattr(doc, "doc_id"), source_type="pdf", blocks=blocks)
        blocks = [
            new_normalized_block(block_id="blk_1", kind="heading", text="Intro", order_index=0, heading_level=1),
            new_normalized_block(block_id="blk_2", kind="paragraph", text="hello world", order_index=1),
            new_normalized_block(block_id="blk_3", kind="code", text="print('x')", order_index=2),
        ]
        return new_normalized_payload(doc_id=getattr(doc, "doc_id"), source_type="markdown", blocks=blocks)


class FakeStructureService:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.raise_error: Exception | None = None

    def derive_sections(self, *, doc: Any, normalized: Any) -> list[Any]:
        self.calls.append(getattr(doc, "doc_id"))
        if self.raise_error:
            raise self.raise_error
        source_type = getattr(normalized, "source_type", "markdown")
        if source_type == "pdf":
            return [
                new_section(
                    section_id="sec_1",
                    doc_id=getattr(doc, "doc_id"),
                    heading_text="1 Introduction",
                    heading_path=["1 Introduction"],
                    page_start=1,
                    page_end=1,
                )
            ]
        return [
            new_section(
                section_id="sec_1",
                doc_id=getattr(doc, "doc_id"),
                heading_text="Intro",
                heading_path=["Intro"],
            )
        ]


class FakeChunkingService:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.raise_error: Exception | None = None

    def derive_chunks(self, *, doc: Any, normalized: Any, sections: list[Any]) -> list[Any]:
        self.calls.append(getattr(doc, "doc_id"))
        if self.raise_error:
            raise self.raise_error
        section = sections[0]
        return [
            new_chunk(
                chunk_id="chk_1",
                doc_id=getattr(doc, "doc_id"),
                section_id=getattr(section, "section_id"),
                heading_path=list(getattr(section, "heading_path")),
                text="document lifecycle preserves persisted evidence and honest readiness",
                page_start=getattr(section, "page_start", None),
                page_end=getattr(section, "page_end", None),
            )
        ]


class FakeIndexPublicationService:
    def __init__(self, vector_index: FakeVectorIndex | None = None) -> None:
        self.calls: list[str] = []
        self.raise_error: Exception | None = None
        self.vector_index = vector_index or FakeVectorIndex()

    def publish(self, *, doc: Any, chunks: list[Any]) -> list[Any]:
        self.calls.append(getattr(doc, "doc_id"))
        if self.raise_error:
            raise self.raise_error
        out = []
        for chunk in chunks:
            index_key = self.vector_index.upsert_chunk(
                chunk_id=getattr(chunk, "chunk_id"),
                text=getattr(chunk, "text"),
                metadata={
                    "doc_id": getattr(chunk, "doc_id"),
                    "section_id": getattr(chunk, "section_id"),
                    "heading_path": list(getattr(chunk, "heading_path")),
                },
            )
            out.append(
                new_index_entry(
                    chunk_id=getattr(chunk, "chunk_id"),
                    doc_id=getattr(chunk, "doc_id"),
                    index_key=index_key,
                )
            )
        return out


class FakeReadinessRepositoryView:
    def __init__(
        self,
        documents: FakeDocumentRepository,
        sections: FakeSectionRepository,
        chunks: FakeChunkRepository,
        index_entries: FakeIndexEntryRepository,
        normalized_docs: set[str] | None = None,
        vector_index: FakeVectorIndex | None = None,
    ) -> None:
        self.documents = documents
        self.sections = sections
        self.chunks = chunks
        self.index_entries = index_entries
        self.normalized_docs = normalized_docs or set()
        self.vector_index = vector_index or FakeVectorIndex()
        self.open_failures: set[str] = set()

    def document_exists(self, doc_id: str) -> bool:
        return self.documents.exists(doc_id)

    def normalized_exists(self, doc_id: str) -> bool:
        return doc_id in self.normalized_docs

    def section_count(self, doc_id: str) -> int:
        return len(self.sections.list_for_document(doc_id))

    def chunk_count(self, doc_id: str) -> int:
        return len(self.chunks.list_for_document(doc_id))

    def index_count(self, doc_id: str) -> int:
        return len(self.index_entries.list_for_document(doc_id))

    def all_chunks_have_valid_owner_links(self, doc_id: str) -> bool:
        sections = {getattr(s, "section_id") for s in self.sections.list_for_document(doc_id)}
        for chunk in self.chunks.list_for_document(doc_id):
            if getattr(chunk, "doc_id", None) != doc_id:
                return False
            if getattr(chunk, "section_id", None) not in sections:
                return False
        return True

    def all_chunks_have_minimum_provenance(self, doc_id: str) -> bool:
        for chunk in self.chunks.list_for_document(doc_id):
            if not getattr(chunk, "doc_id", None):
                return False
            if not list(getattr(chunk, "heading_path", []) or []):
                return False
            has_section = bool(getattr(chunk, "section_id", None))
            has_page = getattr(chunk, "page_start", None) is not None or getattr(chunk, "page_end", None) is not None
            has_offsets = getattr(chunk, "source_offset_start", None) is not None or getattr(chunk, "source_offset_end", None) is not None
            if not (has_section or has_page or has_offsets):
                return False
        return True

    def retrieval_smoke_passes(self, doc_id: str) -> bool:
        chunks = self.chunks.list_for_document(doc_id)
        if not chunks:
            return False
        sample = getattr(chunks[0], "text")
        return bool(self.vector_index.smoke_query(doc_id=doc_id, text=sample[:30], k=1))

    def has_open_failure(self, doc_id: str) -> bool:
        return doc_id in self.open_failures


class FakeReadinessService:
    def __init__(self, view: FakeReadinessRepositoryView) -> None:
        self.view = view

    def evaluate(self, *, doc_id: str) -> bool:
        return (
            self.view.document_exists(doc_id)
            and self.view.normalized_exists(doc_id)
            and self.view.section_count(doc_id) > 0
            and self.view.chunk_count(doc_id) > 0
            and self.view.index_count(doc_id) == self.view.chunk_count(doc_id)
            and self.view.all_chunks_have_valid_owner_links(doc_id)
            and self.view.all_chunks_have_minimum_provenance(doc_id)
            and self.view.retrieval_smoke_passes(doc_id)
            and not self.view.has_open_failure(doc_id)
        )


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def make_upload_context(
    *,
    workspace_id: str = "ws_1",
    filename: str = "test.md",
    title: str = "Test",
    source_type: str = "markdown",
    data: bytes | None = None,
) -> UploadContext:
    raw = data or b"# Intro\n\nhello world\n"
    checksum = sha256_bytes(raw)
    upload_id = "upl_1"
    suffix = Path(filename).suffix or ".bin"
    raw_storage_path = f"data/raw/{workspace_id}/{upload_id}/source{suffix}"
    return UploadContext(
        upload_id=upload_id,
        workspace_id=workspace_id,
        filename=filename,
        title=title,
        source_type=source_type,
        checksum=checksum,
        raw_storage_path=raw_storage_path,
        size_bytes=len(raw),
    )


def make_markdown_stream() -> io.BytesIO:
    return io.BytesIO(
        b"# Intro\n\nDocument lifecycle preserves persisted evidence.\n\n```python\nprint('hi')\n```\n"
    )


def make_pdfish_stream() -> io.BytesIO:
    raw = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n"
    return io.BytesIO(raw)
