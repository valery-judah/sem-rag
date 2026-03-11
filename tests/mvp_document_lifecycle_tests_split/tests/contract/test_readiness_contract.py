from __future__ import annotations

import pytest

from tests.helpers.builders import new_chunk, new_document, new_index_entry, new_section, processing_status
from tests.helpers.fakes import FakeReadinessRepositoryView, FakeReadinessService, FakeVectorIndex


pytestmark = pytest.mark.contract


def _seed_ready_view():
    from tests.helpers.fakes import FakeDocumentRepository, FakeSectionRepository, FakeChunkRepository, FakeIndexEntryRepository
    docs = FakeDocumentRepository()
    secs = FakeSectionRepository()
    chks = FakeChunkRepository()
    idxs = FakeIndexEntryRepository()
    vector = FakeVectorIndex()
    view = FakeReadinessRepositoryView(docs, secs, chks, idxs, normalized_docs=set(), vector_index=vector)
    doc = new_document(doc_id="doc_1", status=processing_status("INDEXED"), ingest_status=processing_status("INDEXED"))
    section = new_section(section_id="sec_1", doc_id="doc_1", heading_path=["Intro"], heading_text="Intro")
    chunk = new_chunk(
        chunk_id="chk_1",
        doc_id="doc_1",
        section_id="sec_1",
        heading_path=["Intro"],
        text="document lifecycle preserves persisted evidence and honest readiness",
        source_offset_start=0,
        source_offset_end=64,
    )
    entry = new_index_entry(chunk_id="chk_1", doc_id="doc_1")
    docs.create(doc)
    secs.replace_for_document("doc_1", [section])
    chks.replace_for_document("doc_1", [chunk])
    idxs.replace_for_document("doc_1", [entry])
    vector.upsert_chunk(
        chunk_id="chk_1",
        text=getattr(chunk, "text"),
        metadata={"doc_id": "doc_1", "section_id": "sec_1", "heading_path": ["Intro"]},
    )
    view.normalized_docs.add("doc_1")
    return view


def test_readiness_predicate_accepts_complete_document():
    view = _seed_ready_view()
    service = FakeReadinessService(view)
    assert service.evaluate(doc_id="doc_1") is True


def test_ready_requires_document_record():
    view = _seed_ready_view()
    del view.documents.docs["doc_1"]
    assert FakeReadinessService(view).evaluate(doc_id="doc_1") is False


def test_ready_requires_normalized_artifact():
    view = _seed_ready_view()
    view.normalized_docs.remove("doc_1")
    assert FakeReadinessService(view).evaluate(doc_id="doc_1") is False


def test_ready_requires_sections():
    view = _seed_ready_view()
    view.sections.replace_for_document("doc_1", [])
    assert FakeReadinessService(view).evaluate(doc_id="doc_1") is False


def test_ready_requires_chunks():
    view = _seed_ready_view()
    view.chunks.replace_for_document("doc_1", [])
    assert FakeReadinessService(view).evaluate(doc_id="doc_1") is False


def test_ready_requires_index_count_to_match_chunk_count():
    view = _seed_ready_view()
    view.index_entries.replace_for_document("doc_1", [])
    assert FakeReadinessService(view).evaluate(doc_id="doc_1") is False


def test_ready_requires_valid_owner_links():
    view = _seed_ready_view()
    bad = new_chunk(
        chunk_id="chk_bad",
        doc_id="doc_1",
        section_id="does_not_exist",
        heading_path=["Intro"],
        text="bad owner links",
        source_offset_start=0,
        source_offset_end=10,
    )
    view.chunks.replace_for_document("doc_1", [bad])
    view.index_entries.replace_for_document("doc_1", [new_index_entry(chunk_id="chk_bad", doc_id="doc_1")])
    assert FakeReadinessService(view).evaluate(doc_id="doc_1") is False


def test_ready_requires_minimum_provenance():
    view = _seed_ready_view()
    bad = new_chunk(
        chunk_id="chk_bad",
        doc_id="doc_1",
        section_id=None,
        heading_path=[],
        text="missing provenance",
        source_offset_start=None,
        source_offset_end=None,
        page_start=None,
        page_end=None,
    )
    view.chunks.replace_for_document("doc_1", [bad])
    view.index_entries.replace_for_document("doc_1", [new_index_entry(chunk_id="chk_bad", doc_id="doc_1")])
    assert FakeReadinessService(view).evaluate(doc_id="doc_1") is False


def test_ready_requires_retrieval_smoke_query_to_pass():
    view = _seed_ready_view()
    view.vector_index.index.clear()
    assert FakeReadinessService(view).evaluate(doc_id="doc_1") is False


def test_ready_rejected_when_open_failure_present():
    view = _seed_ready_view()
    view.open_failures.add("doc_1")
    assert FakeReadinessService(view).evaluate(doc_id="doc_1") is False
