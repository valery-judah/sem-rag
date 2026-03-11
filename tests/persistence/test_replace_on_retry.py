from __future__ import annotations

import pytest

from parity.persistence import (
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlSectionRepository,
)

pytestmark = pytest.mark.persistence


def test_retry_from_normalized_replaces_sections_and_chunks(
    sql_engine,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    sections_repo = SqlSectionRepository(sql_engine)
    chunks_repo = SqlChunkRepository(sql_engine)
    document = persisted_document_factory()
    old_section = section_factory(doc_id=document.doc_id, section_id="old-section")
    new_section = section_factory(
        doc_id=document.doc_id,
        section_id="new-section",
        heading_path=["Replacement"],
        heading_text="Replacement",
    )
    documents.create(document)
    sections_repo.save([old_section])
    chunks_repo.save(
        [
            chunk_factory(
                doc_id=document.doc_id,
                chunk_id="old-chunk",
                section_id=old_section.section_id,
            )
        ],
    )

    sections_repo.replace_for_document(document.doc_id, [new_section])
    chunks_repo.replace_for_document(
        document.doc_id,
        [
            chunk_factory(
                doc_id=document.doc_id,
                chunk_id="new-chunk",
                section_id=new_section.section_id,
                heading_path=["Replacement"],
                text="Replacement chunk.",
            )
        ],
    )

    assert [section.section_id for section in sections_repo.list_for_document(document.doc_id)] == [
        "new-section"
    ]
    assert [chunk.chunk_id for chunk in chunks_repo.list_for_document(document.doc_id)] == [
        "new-chunk"
    ]


def test_double_retry_is_idempotent(
    sql_engine,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    sections_repo = SqlSectionRepository(sql_engine)
    chunks_repo = SqlChunkRepository(sql_engine)
    document = persisted_document_factory()
    section = section_factory(doc_id=document.doc_id, section_id="stable-section")
    chunk = chunk_factory(
        doc_id=document.doc_id,
        chunk_id="stable-chunk",
        section_id=section.section_id,
    )
    documents.create(document)

    sections_repo.replace_for_document(document.doc_id, [section])
    chunks_repo.replace_for_document(document.doc_id, [chunk])
    sections_repo.replace_for_document(document.doc_id, [section])
    chunks_repo.replace_for_document(document.doc_id, [chunk])

    assert sections_repo.list_for_document(document.doc_id) == [section]
    assert chunks_repo.list_for_document(document.doc_id) == [chunk]


def test_retry_does_not_duplicate_child_ownership(
    sql_engine,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    sections_repo = SqlSectionRepository(sql_engine)
    chunks_repo = SqlChunkRepository(sql_engine)
    document = persisted_document_factory()
    documents.create(document)

    for suffix in ("one", "two"):
        section = section_factory(doc_id=document.doc_id, section_id=f"section-{suffix}")
        sections_repo.replace_for_document(document.doc_id, [section])
        chunks_repo.replace_for_document(
            document.doc_id,
            [
                chunk_factory(
                    doc_id=document.doc_id,
                    chunk_id=f"chunk-{suffix}",
                    section_id=section.section_id,
                )
            ],
        )

    sections = sections_repo.list_for_document(document.doc_id)
    chunks = chunks_repo.list_for_document(document.doc_id)

    assert [section.section_id for section in sections] == ["section-two"]
    assert [chunk.chunk_id for chunk in chunks] == ["chunk-two"]
    assert chunks[0].section_id == sections[0].section_id
