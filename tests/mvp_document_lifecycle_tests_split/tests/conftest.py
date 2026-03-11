from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.builders import (
    FIXED_NOW,
    new_chunk,
    new_document,
    new_extracted_artifact,
    new_index_entry,
    new_normalized_block,
    new_normalized_payload,
    new_section,
    processing_status,
)
from tests.helpers.fakes import (
    FakeArtifactStore,
    FakeChunkRepository,
    FakeDocumentRepository,
    FakeExtractionService,
    FakeIndexEntryRepository,
    FakeIndexPublicationService,
    FakeJobsRepository,
    FakeLifecycleEventRepository,
    FakeNormalizationService,
    FakeReadinessRepositoryView,
    FakeReadinessService,
    FakeSectionRepository,
    FakeStructureService,
    FakeChunkingService,
    FakeVectorIndex,
    make_markdown_stream,
    make_pdfish_stream,
    make_upload_context,
)
from tests.helpers.imports import (
    CHUNK_MODEL_CANDIDATES,
    DOCUMENT_MODEL_CANDIDATES,
    DOCUMENT_JOB_CANDIDATES,
    EXTRACTED_ARTIFACT_CANDIDATES,
    INDEX_ENTRY_MODEL_CANDIDATES,
    NORMALIZED_BLOCK_CANDIDATES,
    NORMALIZED_PAYLOAD_CANDIDATES,
    PROCESSING_STATUS_CANDIDATES,
    SECTION_MODEL_CANDIDATES,
    TERMINAL_STATUS_CANDIDATES,
    IN_FLIGHT_STATUS_CANDIDATES,
    import_attr_any,
    maybe_import_attr_any,
    enum_member_names,
)


@pytest.fixture
def fixed_now():
    return FIXED_NOW


@pytest.fixture
def tmp_artifact_store(tmp_path):
    return FakeArtifactStore(base_dir=tmp_path)


@pytest.fixture
def artifact_store():
    return FakeArtifactStore()


@pytest.fixture
def document_repo():
    return FakeDocumentRepository()


@pytest.fixture
def lifecycle_event_repo():
    return FakeLifecycleEventRepository()


@pytest.fixture
def section_repo():
    return FakeSectionRepository()


@pytest.fixture
def chunk_repo():
    return FakeChunkRepository()


@pytest.fixture
def index_entry_repo():
    return FakeIndexEntryRepository()


@pytest.fixture
def jobs_repo():
    return FakeJobsRepository()


@pytest.fixture
def vector_index():
    return FakeVectorIndex()


@pytest.fixture
def extraction_service():
    return FakeExtractionService()


@pytest.fixture
def normalization_service():
    return FakeNormalizationService()


@pytest.fixture
def structure_service():
    return FakeStructureService()


@pytest.fixture
def chunking_service():
    return FakeChunkingService()


@pytest.fixture
def index_publication_service(vector_index):
    return FakeIndexPublicationService(vector_index=vector_index)


@pytest.fixture
def readiness_view(document_repo, section_repo, chunk_repo, index_entry_repo, vector_index):
    return FakeReadinessRepositoryView(
        documents=document_repo,
        sections=section_repo,
        chunks=chunk_repo,
        index_entries=index_entry_repo,
        normalized_docs=set(),
        vector_index=vector_index,
    )


@pytest.fixture
def readiness_service(readiness_view):
    return FakeReadinessService(readiness_view)


@pytest.fixture
def markdown_stream():
    return make_markdown_stream()


@pytest.fixture
def pdfish_stream():
    return make_pdfish_stream()


@pytest.fixture
def markdown_upload_context():
    return make_upload_context(filename="simple.md", title="Simple", source_type="markdown")


@pytest.fixture
def pdf_upload_context():
    return make_upload_context(filename="book.pdf", title="Book", source_type="pdf", data=b"%PDF-1.4 fake\n")


@pytest.fixture
def statuses():
    enum_cls = import_attr_any(PROCESSING_STATUS_CANDIDATES)
    return {name: getattr(enum_cls, name) for name in enum_member_names(enum_cls)}


@pytest.fixture
def in_flight_statuses():
    return maybe_import_attr_any(IN_FLIGHT_STATUS_CANDIDATES)


@pytest.fixture
def terminal_statuses():
    return maybe_import_attr_any(TERMINAL_STATUS_CANDIDATES)


@pytest.fixture
def document_factory():
    def _make(**overrides):
        return new_document(**overrides)
    return _make


@pytest.fixture
def section_factory():
    def _make(**overrides):
        return new_section(**overrides)
    return _make


@pytest.fixture
def chunk_factory():
    def _make(**overrides):
        return new_chunk(**overrides)
    return _make


@pytest.fixture
def index_entry_factory():
    def _make(**overrides):
        return new_index_entry(**overrides)
    return _make


@pytest.fixture
def normalized_block_factory():
    def _make(**overrides):
        return new_normalized_block(**overrides)
    return _make


@pytest.fixture
def normalized_payload_factory():
    def _make(**overrides):
        return new_normalized_payload(**overrides)
    return _make


@pytest.fixture
def extracted_artifact_factory():
    def _make(**overrides):
        return new_extracted_artifact(**overrides)
    return _make


@pytest.fixture
def ready_document_bundle(document_repo, section_repo, chunk_repo, index_entry_repo, vector_index, readiness_view, document_factory, section_factory, chunk_factory, index_entry_factory):
    doc = document_factory(doc_id="doc_ready", source_type="markdown", status=processing_status("INDEXED"), ingest_status=processing_status("INDEXED"))
    document_repo.create(doc)
    sec = section_factory(section_id="sec_ready", doc_id="doc_ready", heading_path=["Intro"], heading_text="Intro")
    chunk = chunk_factory(
        chunk_id="chk_ready",
        doc_id="doc_ready",
        section_id="sec_ready",
        heading_path=["Intro"],
        text="document lifecycle preserves persisted evidence and honest readiness",
    )
    section_repo.replace_for_document("doc_ready", [sec])
    chunk_repo.replace_for_document("doc_ready", [chunk])
    vector_index.upsert_chunk(
        chunk_id="chk_ready",
        text=getattr(chunk, "text"),
        metadata={"doc_id": "doc_ready", "section_id": "sec_ready", "heading_path": ["Intro"]},
    )
    entry = index_entry_factory(chunk_id="chk_ready", doc_id="doc_ready")
    index_entry_repo.replace_for_document("doc_ready", [entry])
    readiness_view.normalized_docs.add("doc_ready")
    return {"document": doc, "section": sec, "chunk": chunk, "entry": entry}


@pytest.fixture
def fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures" / "docs"
