from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

import parity._contracts as contracts
from parity.lifecycle import (
    FailureCategory,
    LifecycleEvent,
    LifecycleStage,
    ProcessingStatus,
)

pytestmark = pytest.mark.contract


def test_lifecycle_event_requires_stage_and_to_status() -> None:
    with pytest.raises(ValidationError) as excinfo:
        LifecycleEvent.model_validate(
            {
                "event_id": "event-1",
                "doc_id": "doc-1",
                "occurred_at": datetime(2026, 3, 11, tzinfo=UTC),
            }
        )

    message = str(excinfo.value)
    assert "stage" in message
    assert "to_status" in message


def test_lifecycle_stage_enum_values_are_stable() -> None:
    assert [stage.value for stage in LifecycleStage] == [
        "upload",
        "register",
        "extract",
        "normalize",
        "chunk",
        "index",
        "readiness",
    ]


def test_failure_category_enum_covers_expected_failure_classes() -> None:
    assert [category.value for category in FailureCategory] == [
        "validation",
        "unsupported_input",
        "processing",
        "internal",
    ]


def test_lifecycle_event_detail_defaults_to_mapping() -> None:
    event = LifecycleEvent(
        event_id="event-1",
        doc_id="doc-1",
        stage=LifecycleStage.REGISTER,
        from_status=ProcessingStatus.UPLOADED,
        to_status=ProcessingStatus.REGISTERED,
        occurred_at=datetime(2026, 3, 11, tzinfo=UTC),
    )

    assert event.detail == {}


def test_lifecycle_event_accepts_failed_transition_with_failure_category() -> None:
    event = LifecycleEvent(
        event_id="event-1",
        doc_id="doc-1",
        stage=LifecycleStage.EXTRACT,
        from_status=ProcessingStatus.EXTRACTING,
        to_status=ProcessingStatus.FAILED,
        occurred_at=datetime(2026, 3, 11, tzinfo=UTC),
        failure_category=FailureCategory.PROCESSING,
        detail={"reason": "Malformed PDF"},
    )

    assert event.stage is LifecycleStage.EXTRACT
    assert event.failure_category is FailureCategory.PROCESSING


def test_lifecycle_event_rejects_missing_failure_category_for_failed_transition() -> None:
    with pytest.raises(
        ValidationError,
        match="failed lifecycle events must include a failure_category",
    ):
        LifecycleEvent(
            event_id="event-1",
            doc_id="doc-1",
            stage=LifecycleStage.EXTRACT,
            from_status=ProcessingStatus.EXTRACTING,
            to_status=ProcessingStatus.FAILED,
            occurred_at=datetime(2026, 3, 11, tzinfo=UTC),
            detail={"reason": "Malformed PDF"},
        )


def test_lifecycle_event_rejects_failure_category_for_non_failed_transition() -> None:
    with pytest.raises(
        ValidationError,
        match="non-failed lifecycle events must not include a failure_category",
    ):
        LifecycleEvent(
            event_id="event-1",
            doc_id="doc-1",
            stage=LifecycleStage.REGISTER,
            from_status=ProcessingStatus.UPLOADED,
            to_status=ProcessingStatus.REGISTERED,
            occurred_at=datetime(2026, 3, 11, tzinfo=UTC),
            failure_category=FailureCategory.VALIDATION,
            detail={},
        )


def test_runtime_models_are_internal_not_contract_models() -> None:
    assert not hasattr(contracts, "LifecycleEvent")
    assert not hasattr(contracts, "LifecycleStage")
    assert not hasattr(contracts, "FailureCategory")
