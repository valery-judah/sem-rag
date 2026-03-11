from __future__ import annotations

from datetime import UTC, datetime

import pytest

from parity.indexing import IndexEntry
from parity.persistence import (
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
)

pytestmark = pytest.mark.persistence


def test_index_entries_round_trip_for_document(
    sql_engine,
    persisted_document_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    index_entries = SqlIndexEntryRepository(sql_engine)
    document = persisted_document_factory()
    documents.create(document)
    chunks.save([chunk_factory(doc_id=document.doc_id)])

    published = [
        IndexEntry(
            chunk_id="chunk-1",
            doc_id=document.doc_id,
            index_backend="sqlite-json-vector",
            index_key="chunk-1",
            index_version="v1",
            published_at=datetime(2026, 3, 11, tzinfo=UTC),
        )
    ]

    index_entries.replace_for_document(document.doc_id, published)

    assert index_entries.list_for_document(document.doc_id) == published


def test_replace_for_document_removes_prior_index_entries(
    sql_engine,
    persisted_document_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    index_entries = SqlIndexEntryRepository(sql_engine)
    document = persisted_document_factory()
    documents.create(document)
    chunks.save(
        [
            chunk_factory(doc_id=document.doc_id, chunk_id="chunk-1"),
            chunk_factory(doc_id=document.doc_id, chunk_id="chunk-2", ordinal=1),
        ]
    )
    index_entries.replace_for_document(
        document.doc_id,
        [
            IndexEntry(
                chunk_id="chunk-1",
                doc_id=document.doc_id,
                index_backend="sqlite-json-vector",
                index_key="chunk-1",
                index_version="v1",
                published_at=datetime(2026, 3, 11, tzinfo=UTC),
            )
        ],
    )

    replacement = [
        IndexEntry(
            chunk_id="chunk-2",
            doc_id=document.doc_id,
            index_backend="sqlite-json-vector",
            index_key="chunk-2",
            index_version="v2",
            published_at=datetime(2026, 3, 11, 1, tzinfo=UTC),
        )
    ]
    index_entries.replace_for_document(document.doc_id, replacement)

    assert index_entries.list_for_document(document.doc_id) == replacement


def test_replace_for_document_rejects_cross_document_index_entries(sql_engine) -> None:
    repository = SqlIndexEntryRepository(sql_engine)

    with pytest.raises(ValueError, match="must belong to the target document"):
        repository.replace_for_document(
            "doc-1",
            [
                IndexEntry(
                    chunk_id="chunk-1",
                    doc_id="doc-2",
                    index_backend="sqlite-json-vector",
                    index_key="chunk-1",
                    index_version="v1",
                    published_at=datetime(2026, 3, 11, tzinfo=UTC),
                )
            ],
        )
