from __future__ import annotations

import pytest

from tests.helpers.builders import new_chunk, new_document, new_index_entry, new_section, processing_status


pytestmark = [pytest.mark.pipeline, pytest.mark.slow]


def test_pdf_ready_chunks_can_have_page_oriented_provenance(document_repo, section_repo, chunk_repo, index_entry_repo, vector_index, readiness_view, readiness_service):
    doc = new_document(doc_id="doc_pdf", source_type="pdf", filename="book.pdf", status=processing_status("INDEXED"), ingest_status=processing_status("INDEXED"))
    section = new_section(section_id="sec_pdf", doc_id="doc_pdf", heading_path=["1 Introduction"], heading_text="1 Introduction", page_start=1, page_end=2)
    chunk = new_chunk(
        chunk_id="chk_pdf",
        doc_id="doc_pdf",
        section_id="sec_pdf",
        heading_path=["1 Introduction"],
        text="Document lifecycle for pdf pages.",
        page_start=1,
        page_end=1,
        source_offset_start=None,
        source_offset_end=None,
    )
    entry = new_index_entry(chunk_id="chk_pdf", doc_id="doc_pdf")
    document_repo.create(doc)
    section_repo.replace_for_document("doc_pdf", [section])
    chunk_repo.replace_for_document("doc_pdf", [chunk])
    index_entry_repo.replace_for_document("doc_pdf", [entry])
    vector_index.upsert_chunk(
        chunk_id="chk_pdf",
        text=getattr(chunk, "text"),
        metadata={"doc_id": "doc_pdf", "section_id": "sec_pdf", "heading_path": ["1 Introduction"]},
    )
    readiness_view.normalized_docs.add("doc_pdf")
    assert readiness_service.evaluate(doc_id="doc_pdf") is True
