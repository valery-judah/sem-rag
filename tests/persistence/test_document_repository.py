from __future__ import annotations

import pytest
import sqlalchemy as sa

from doc_forge.corpus import SourceType
from doc_forge.lifecycle import ProcessingStatus
from doc_forge.persistence import (
    SqlDocumentRepository,
)

pytestmark = pytest.mark.persistence


from tests.persistence.conftest import PersistedDocumentFactory


def test_create_and_get_document_round_trip(
    sql_engine: sa.Engine,
    persisted_document_factory: PersistedDocumentFactory,
) -> None:
    repository = SqlDocumentRepository(sql_engine)
    document = persisted_document_factory()

    repository.create(document)

    loaded = repository.get(document.doc_id)

    assert loaded == document


def test_workspace_isolation_filters_documents(
    sql_engine: sa.Engine,
    persisted_document_factory: PersistedDocumentFactory,
) -> None:
    repository = SqlDocumentRepository(sql_engine)
    repository.create(persisted_document_factory(doc_id="doc-1", workspace_id="workspace-1"))
    repository.create(persisted_document_factory(doc_id="doc-2", workspace_id="workspace-2"))

    loaded = repository.list_by_workspace("workspace-1")

    assert [document.doc_id for document in loaded] == ["doc-1"]


def test_list_by_workspace_returns_persisted_documents(
    sql_engine: sa.Engine,
    persisted_document_factory: PersistedDocumentFactory,
) -> None:
    repository = SqlDocumentRepository(sql_engine)
    expected = [
        persisted_document_factory(doc_id="doc-1"),
        persisted_document_factory(
            doc_id="doc-2",
            filename="doc-2.md",
            source_type=SourceType.MARKDOWN,
            storage_ref="file:///tmp/doc-2.md",
        ),
    ]

    for document in expected:
        repository.create(document)

    loaded = repository.list_by_workspace("workspace-1")

    assert loaded == expected


def test_update_status_clears_failure_fields_on_non_failed_status(
    sql_engine: sa.Engine,
    persisted_document_factory: PersistedDocumentFactory,
) -> None:
    repository = SqlDocumentRepository(sql_engine)
    document = persisted_document_factory(
        ingest_status=ProcessingStatus.FAILED,
        failure_code="extract_failed",
        failure_detail="No usable text layer",
    )
    repository.create(document)

    repository.update_status(
        doc_id=document.doc_id,
        status=ProcessingStatus.NORMALIZED,
    )

    loaded = repository.get(document.doc_id)

    assert loaded is not None
    assert loaded.ingest_status is ProcessingStatus.NORMALIZED
    assert loaded.failure_code is None
    assert loaded.failure_detail is None


def test_update_status_persists_failure_code_and_detail(
    sql_engine: sa.Engine,
    persisted_document_factory: PersistedDocumentFactory,
) -> None:
    repository = SqlDocumentRepository(sql_engine)
    document = persisted_document_factory()
    repository.create(document)

    repository.update_status(
        doc_id=document.doc_id,
        status=ProcessingStatus.FAILED,
        failure_code="extract_failed",
        failure_detail="No usable text layer",
    )

    loaded = repository.get(document.doc_id)

    assert loaded is not None
    assert loaded.ingest_status is ProcessingStatus.FAILED
    assert loaded.failure_code == "extract_failed"
    assert loaded.failure_detail == "No usable text layer"
