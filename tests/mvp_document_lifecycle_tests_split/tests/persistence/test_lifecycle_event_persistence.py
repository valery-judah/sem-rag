from __future__ import annotations

from datetime import datetime, timezone

import pytest

from tests.helpers.imports import LIFECYCLE_EVENT_CANDIDATES, construct_with_supported_kwargs, import_attr_any


pytestmark = pytest.mark.persistence


def test_lifecycle_event_repository_appends_and_filters_by_document(lifecycle_event_repo):
    event_cls = import_attr_any(LIFECYCLE_EVENT_CANDIDATES)
    event1 = construct_with_supported_kwargs(
        event_cls,
        event_id="evt_1",
        doc_id="doc_1",
        stage="register",
        from_status="UPLOADED",
        to_status="REGISTERED",
        occurred_at=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
        detail={"filename": "a.md"},
    )
    event2 = construct_with_supported_kwargs(
        event_cls,
        event_id="evt_2",
        doc_id="doc_2",
        stage="extract",
        from_status="REGISTERED",
        to_status="EXTRACTING",
        occurred_at=datetime(2026, 3, 10, 12, 1, tzinfo=timezone.utc),
        detail={},
    )
    lifecycle_event_repo.append(event1)
    lifecycle_event_repo.append(event2)
    events = lifecycle_event_repo.list_for_document("doc_1")
    assert [getattr(event, "event_id") for event in events] == ["evt_1"]


def test_lifecycle_event_detail_can_preserve_operator_usable_failure_payload(lifecycle_event_repo):
    event_cls = import_attr_any(LIFECYCLE_EVENT_CANDIDATES)
    event = construct_with_supported_kwargs(
        event_cls,
        event_id="evt_1",
        doc_id="doc_1",
        stage="extract",
        from_status="REGISTERED",
        to_status="FAILED",
        occurred_at=datetime(2026, 3, 10, 12, 1, tzinfo=timezone.utc),
        detail={"error_code": "EXTRACTION_FAILURE", "error_detail": "malformed pdf"},
    )
    lifecycle_event_repo.append(event)
    loaded = lifecycle_event_repo.list_for_document("doc_1")[0]
    assert getattr(loaded, "detail")["error_code"] == "EXTRACTION_FAILURE"
    assert "malformed" in getattr(loaded, "detail")["error_detail"]
