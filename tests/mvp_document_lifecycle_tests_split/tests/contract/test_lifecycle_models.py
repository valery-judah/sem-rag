from __future__ import annotations

from datetime import datetime, timezone

import pytest

from tests.helpers.imports import (
    FAILURE_CATEGORY_CANDIDATES,
    LIFECYCLE_EVENT_CANDIDATES,
    LIFECYCLE_STAGE_CANDIDATES,
    enum_member_names,
    import_attr_any,
)
from tests.helpers.imports import construct_with_supported_kwargs


pytestmark = pytest.mark.contract


def test_lifecycle_stage_enum_contains_expected_stages():
    enum_cls = import_attr_any(LIFECYCLE_STAGE_CANDIDATES)
    assert enum_member_names(enum_cls) >= {
        "REGISTER",
        "EXTRACT",
        "NORMALIZE",
        "SECTIONIZE",
        "CHUNK",
        "INDEX",
        "READY",
    }


def test_failure_category_enum_contains_expected_categories():
    enum_cls = import_attr_any(FAILURE_CATEGORY_CANDIDATES)
    names = enum_member_names(enum_cls)
    assert names >= {
        "UNSUPPORTED_INPUT",
        "RAW_STORAGE_FAILURE",
        "REGISTRATION_FAILURE",
        "EXTRACTION_FAILURE",
        "NORMALIZATION_FAILURE",
        "SECTIONING_FAILURE",
        "CHUNKING_FAILURE",
        "INDEX_PUBLICATION_FAILURE",
        "READINESS_VALIDATION_FAILURE",
        "INTEGRITY_FAILURE",
        "INTERNAL_ERROR",
    }


def test_lifecycle_event_can_be_constructed_with_detail_mapping():
    event_cls = import_attr_any(LIFECYCLE_EVENT_CANDIDATES)
    event = construct_with_supported_kwargs(
        event_cls,
        event_id="evt_1",
        doc_id="doc_123",
        stage="extract",
        from_status="REGISTERED",
        to_status="EXTRACTING",
        occurred_at=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
        detail={"job_id": "job_1"},
    )
    assert getattr(event, "doc_id") == "doc_123"
    assert getattr(event, "stage") in {"extract", "EXTRACT", "extracting"}
    assert getattr(event, "to_status") in {"EXTRACTING", "ProcessingStatus.EXTRACTING"} or hasattr(getattr(event, "to_status"), "name")


def test_lifecycle_event_exposes_append_only_fields():
    event_cls = import_attr_any(LIFECYCLE_EVENT_CANDIDATES)
    event = construct_with_supported_kwargs(
        event_cls,
        event_id="evt_1",
        doc_id="doc_123",
        stage="normalize",
        from_status="EXTRACTING",
        to_status="NORMALIZED",
        occurred_at=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
        detail={"payload_path": "data/normalized/ws/doc/normalized.json"},
    )
    assert hasattr(event, "event_id")
    assert hasattr(event, "doc_id")
    assert hasattr(event, "occurred_at")
    assert hasattr(event, "detail")
