from __future__ import annotations

import pytest

from parity.persistence import (
    DocumentJobStatus,
    SqlDocumentJobRepository,
    SqlDocumentRepository,
)

pytestmark = pytest.mark.persistence


def test_document_job_round_trip(
    sql_engine,
    persisted_document_factory,
    document_job_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    jobs = SqlDocumentJobRepository(sql_engine)
    document = persisted_document_factory()
    job = document_job_factory(doc_id=document.doc_id)
    documents.create(document)

    jobs.create(job)

    assert jobs.get(job.job_id) == job


def test_document_job_update_persists_attempt_count_and_error_detail(
    sql_engine,
    persisted_document_factory,
    document_job_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    jobs = SqlDocumentJobRepository(sql_engine)
    document = persisted_document_factory()
    job = document_job_factory(doc_id=document.doc_id)
    documents.create(document)
    jobs.create(job)

    updated = job.model_copy(
        update={
            "status": DocumentJobStatus.FAILED,
            "attempt_count": 2,
            "error_code": "extract_failed",
            "error_detail": "Parser raised ValueError",
        }
    )
    jobs.update(updated)

    loaded = jobs.get(job.job_id)

    assert loaded == updated
