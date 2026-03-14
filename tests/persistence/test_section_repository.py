from __future__ import annotations

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from doc_forge.corpus import Section
from doc_forge.persistence import (
    SqlDocumentRepository,
    SqlSectionRepository,
)
from tests.persistence.conftest import PersistedDocumentFactory, SectionFactory

pytestmark = pytest.mark.persistence


def test_sections_round_trip_preserves_parent_child_links(
    sql_engine: Engine,
    persisted_document_factory: PersistedDocumentFactory,
    section_factory: SectionFactory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    sections_repo = SqlSectionRepository(sql_engine)
    document = persisted_document_factory()
    sections = [
        section_factory(doc_id=document.doc_id, section_id="doc-1-section-1"),
        section_factory(
            doc_id=document.doc_id,
            section_id="doc-1-section-2",
            parent_section_id="doc-1-section-1",
            heading_path=["Chapter 1", "Overview"],
            depth=1,
            heading_text="Overview",
            page_start=2,
            page_end=3,
            source_start_offset=10,
            source_end_offset=42,
            structure_confidence=0.9,
        ),
    ]
    documents.create(document)

    sections_repo.save(sections)

    loaded = sections_repo.list_for_document(document.doc_id)

    assert loaded == sections
    assert isinstance(loaded[0], Section)


def test_optional_section_fields_round_trip_as_none(
    sql_engine: Engine,
    persisted_document_factory: PersistedDocumentFactory,
    section_factory: SectionFactory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    sections_repo = SqlSectionRepository(sql_engine)
    document = persisted_document_factory()
    section = section_factory(
        doc_id=document.doc_id,
        heading_path=["Appendix"],
        depth=0,
        heading_text=None,
        page_start=None,
        page_end=None,
        source_start_offset=None,
        source_end_offset=None,
        structure_confidence=None,
    )
    documents.create(document)

    sections_repo.save([section])

    loaded = sections_repo.list_for_document(document.doc_id)[0]

    assert loaded.heading_text is None
    assert loaded.page_start is None
    assert loaded.structure_confidence is None


def test_replace_for_document_removes_prior_sections(
    sql_engine: Engine,
    persisted_document_factory: PersistedDocumentFactory,
    section_factory: SectionFactory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    sections_repo = SqlSectionRepository(sql_engine)
    document = persisted_document_factory()
    documents.create(document)
    sections_repo.save(
        [
            section_factory(doc_id=document.doc_id, section_id="old-section-1"),
            section_factory(doc_id=document.doc_id, section_id="old-section-2"),
        ],
    )

    replacement = [
        section_factory(
            doc_id=document.doc_id,
            section_id="new-section-1",
            heading_path=["Replacement"],
            heading_text="Replacement",
        )
    ]
    sections_repo.replace_for_document(document.doc_id, replacement)

    assert sections_repo.list_for_document(document.doc_id) == replacement


def test_replace_for_document_rejects_cross_document_sections(
    sql_engine: Engine,
    persisted_document_factory: PersistedDocumentFactory,
    section_factory: SectionFactory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    sections_repo = SqlSectionRepository(sql_engine)
    document = persisted_document_factory()
    documents.create(document)

    with pytest.raises(ValueError, match="target document"):
        sections_repo.replace_for_document(
            document.doc_id,
            [section_factory(doc_id="doc-2", section_id="doc-2-section-1")],
        )


def test_section_save_requires_existing_document(
    sql_engine: Engine,
    section_factory: SectionFactory,
) -> None:
    sections_repo = SqlSectionRepository(sql_engine)

    with pytest.raises(IntegrityError):
        sections_repo.save([section_factory(doc_id="missing-doc", section_id="section-1")])
