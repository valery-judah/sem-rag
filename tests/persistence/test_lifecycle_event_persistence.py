from __future__ import annotations

import pytest

from doc_forge.lifecycle import ProcessingStatus
from doc_forge.lifecycle.models import FailureCategory, LifecycleStage
from doc_forge.persistence import SqlDocumentRepository, SqlLifecycleEventRepository

pytestmark = pytest.mark.persistence


def test_lifecycle_event_round_trip_preserves_order_and_failure_category(
    sql_engine,
    persisted_document_factory,
    lifecycle_event_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    events = SqlLifecycleEventRepository(sql_engine)
    document = persisted_document_factory()
    documents.create(document)
    registered = lifecycle_event_factory(
        doc_id=document.doc_id,
        event_id="event-1",
        occurred_at=document.created_at,
    )
    failed = lifecycle_event_factory(
        doc_id=document.doc_id,
        event_id="event-2",
        stage=LifecycleStage.EXTRACT,
        from_status=ProcessingStatus.REGISTERED,
        to_status=ProcessingStatus.FAILED,
        failure_category=FailureCategory.PROCESSING,
        occurred_at=document.created_at.replace(hour=2),
        detail={"reason": "decode failure"},
    )

    events.append(failed)
    events.append(registered)

    loaded = events.list_for_document(document.doc_id)

    assert [event.event_id for event in loaded] == ["event-1", "event-2"]
    assert loaded[1].failure_category is FailureCategory.PROCESSING
    assert loaded[1].detail == {"reason": "decode failure"}
