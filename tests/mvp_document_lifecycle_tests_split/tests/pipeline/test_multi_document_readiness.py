from __future__ import annotations

import pytest

from tests.helpers.builders import new_chunk, new_document, new_index_entry, new_section, processing_status


pytestmark = [pytest.mark.pipeline, pytest.mark.slow]


def test_readiness_and_smoke_query_are_document_scoped(document_repo, section_repo, chunk_repo, index_entry_repo, vector_index, readiness_view, readiness_service):
    doc1 = new_document(doc_id="doc_1", source_type="markdown", status=processing_status("INDEXED"), ingest_status=processing_status("INDEXED"))
    doc2 = new_document(doc_id="doc_2", source_type="markdown", status=processing_status("INDEXED"), ingest_status=processing_status("INDEXED"))
    document_repo.create(doc1)
    document_repo.create(doc2)

    section_repo.replace_for_document("doc_1", [new_section(section_id="sec_1", doc_id="doc_1", heading_path=["A"], heading_text="A")])
    section_repo.replace_for_document("doc_2", [new_section(section_id="sec_2", doc_id="doc_2", heading_path=["B"], heading_text="B")])

    chunk_repo.replace_for_document("doc_1", [new_chunk(chunk_id="chk_1", doc_id="doc_1", section_id="sec_1", heading_path=["A"], text="alpha content", source_offset_start=0, source_offset_end=5)])
    chunk_repo.replace_for_document("doc_2", [new_chunk(chunk_id="chk_2", doc_id="doc_2", section_id="sec_2", heading_path=["B"], text="beta content", source_offset_start=0, source_offset_end=4)])

    index_entry_repo.replace_for_document("doc_1", [new_index_entry(chunk_id="chk_1", doc_id="doc_1")])
    index_entry_repo.replace_for_document("doc_2", [new_index_entry(chunk_id="chk_2", doc_id="doc_2")])

    vector_index.upsert_chunk(chunk_id="chk_1", text="alpha content", metadata={"doc_id": "doc_1", "section_id": "sec_1", "heading_path": ["A"]})
    vector_index.upsert_chunk(chunk_id="chk_2", text="beta content", metadata={"doc_id": "doc_2", "section_id": "sec_2", "heading_path": ["B"]})

    readiness_view.normalized_docs.update({"doc_1", "doc_2"})

    assert readiness_service.evaluate(doc_id="doc_1") is True
    assert readiness_service.evaluate(doc_id="doc_2") is True
    assert vector_index.smoke_query(doc_id="doc_1", text="alpha", k=1)[0]["doc_id"] == "doc_1"
    assert vector_index.smoke_query(doc_id="doc_2", text="beta", k=1)[0]["doc_id"] == "doc_2"
