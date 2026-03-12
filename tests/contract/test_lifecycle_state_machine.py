from __future__ import annotations

import pytest

from doc_forge.lifecycle import (
    InvalidLifecycleTransitionError,
    ProcessingStatus,
    allowed_next_processing_statuses,
    can_transition_processing_status,
    require_processing_status_transition,
)

pytestmark = pytest.mark.contract


@pytest.mark.parametrize(
    ("current", "new"),
    [
        (ProcessingStatus.UPLOADED, ProcessingStatus.REGISTERED),
        (ProcessingStatus.REGISTERED, ProcessingStatus.EXTRACTING),
        (ProcessingStatus.EXTRACTING, ProcessingStatus.NORMALIZED),
        (ProcessingStatus.NORMALIZED, ProcessingStatus.CHUNKED),
        (ProcessingStatus.CHUNKED, ProcessingStatus.INDEXED),
        (ProcessingStatus.INDEXED, ProcessingStatus.READY),
    ],
)
def test_linear_happy_path_transitions_are_allowed(
    current: ProcessingStatus,
    new: ProcessingStatus,
) -> None:
    assert can_transition_processing_status(current, new)
    require_processing_status_transition(current, new)


@pytest.mark.parametrize("current", sorted(ProcessingStatus))
def test_allowed_next_processing_statuses_match_locked_transition_table(
    current: ProcessingStatus,
) -> None:
    expected = {
        ProcessingStatus.UPLOADED: frozenset({ProcessingStatus.REGISTERED}),
        ProcessingStatus.REGISTERED: frozenset(
            {ProcessingStatus.EXTRACTING, ProcessingStatus.FAILED}
        ),
        ProcessingStatus.EXTRACTING: frozenset(
            {ProcessingStatus.NORMALIZED, ProcessingStatus.FAILED}
        ),
        ProcessingStatus.NORMALIZED: frozenset({ProcessingStatus.CHUNKED, ProcessingStatus.FAILED}),
        ProcessingStatus.CHUNKED: frozenset({ProcessingStatus.INDEXED, ProcessingStatus.FAILED}),
        ProcessingStatus.INDEXED: frozenset({ProcessingStatus.READY, ProcessingStatus.FAILED}),
        ProcessingStatus.READY: frozenset(),
        ProcessingStatus.FAILED: frozenset(),
    }

    assert allowed_next_processing_statuses(current) == expected[current]


@pytest.mark.parametrize(
    "current",
    [
        ProcessingStatus.REGISTERED,
        ProcessingStatus.EXTRACTING,
        ProcessingStatus.NORMALIZED,
        ProcessingStatus.CHUNKED,
        ProcessingStatus.INDEXED,
    ],
)
def test_failed_reachable_from_each_in_flight_status(current: ProcessingStatus) -> None:
    assert can_transition_processing_status(current, ProcessingStatus.FAILED)


def test_uploaded_to_failed_is_rejected() -> None:
    with pytest.raises(
        InvalidLifecycleTransitionError,
        match="cannot transition processing status from uploaded to failed",
    ):
        require_processing_status_transition(
            ProcessingStatus.UPLOADED,
            ProcessingStatus.FAILED,
        )


@pytest.mark.parametrize(
    ("current", "new"),
    [
        (ProcessingStatus.REGISTERED, ProcessingStatus.CHUNKED),
        (ProcessingStatus.EXTRACTING, ProcessingStatus.INDEXED),
    ],
)
def test_skip_transition_is_rejected(
    current: ProcessingStatus,
    new: ProcessingStatus,
) -> None:
    assert not can_transition_processing_status(current, new)
    with pytest.raises(InvalidLifecycleTransitionError):
        require_processing_status_transition(current, new)


@pytest.mark.parametrize(
    ("current", "new"),
    [
        (ProcessingStatus.READY, ProcessingStatus.CHUNKED),
        (ProcessingStatus.READY, ProcessingStatus.FAILED),
        (ProcessingStatus.FAILED, ProcessingStatus.READY),
    ],
)
def test_regression_from_terminal_state_is_rejected(
    current: ProcessingStatus,
    new: ProcessingStatus,
) -> None:
    assert not can_transition_processing_status(current, new)
    with pytest.raises(InvalidLifecycleTransitionError):
        require_processing_status_transition(current, new)
