from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from parity.lifecycle import (
    IN_FLIGHT_PROCESSING_STATUSES,
    TERMINAL_PROCESSING_STATUSES,
    FailureCategory,
    LifecycleEvent,
    LifecycleStage,
    ProcessingStatus,
    allowed_next_processing_statuses,
)


def test_status_sets_capture_in_flight_and_terminal_states() -> None:
    assert IN_FLIGHT_PROCESSING_STATUSES == frozenset(
        {
            ProcessingStatus.REGISTERED,
            ProcessingStatus.EXTRACTING,
            ProcessingStatus.NORMALIZED,
            ProcessingStatus.CHUNKED,
            ProcessingStatus.INDEXED,
        }
    )
    assert TERMINAL_PROCESSING_STATUSES == frozenset(
        {
            ProcessingStatus.READY,
            ProcessingStatus.FAILED,
        }
    )


def test_allowed_next_processing_statuses_matches_locked_transition_table() -> None:
    assert allowed_next_processing_statuses(ProcessingStatus.UPLOADED) == frozenset(
        {ProcessingStatus.REGISTERED}
    )
    assert allowed_next_processing_statuses(ProcessingStatus.INDEXED) == frozenset(
        {ProcessingStatus.READY, ProcessingStatus.FAILED}
    )


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
