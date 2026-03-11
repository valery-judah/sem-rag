from __future__ import annotations

import pytest

from parity.lifecycle import (
    IN_FLIGHT_PROCESSING_STATUSES,
    TERMINAL_PROCESSING_STATUSES,
    ProcessingStatus,
)

pytestmark = pytest.mark.contract


def test_in_flight_statuses_are_registered_through_indexed() -> None:
    assert IN_FLIGHT_PROCESSING_STATUSES == frozenset(
        {
            ProcessingStatus.REGISTERED,
            ProcessingStatus.EXTRACTING,
            ProcessingStatus.NORMALIZED,
            ProcessingStatus.CHUNKED,
            ProcessingStatus.INDEXED,
        }
    )


def test_terminal_statuses_are_ready_and_failed() -> None:
    assert TERMINAL_PROCESSING_STATUSES == frozenset(
        {
            ProcessingStatus.READY,
            ProcessingStatus.FAILED,
        }
    )


def test_uploaded_is_not_in_flight_or_terminal() -> None:
    assert ProcessingStatus.UPLOADED not in IN_FLIGHT_PROCESSING_STATUSES
    assert ProcessingStatus.UPLOADED not in TERMINAL_PROCESSING_STATUSES


def test_status_sets_are_disjoint() -> None:
    assert IN_FLIGHT_PROCESSING_STATUSES.isdisjoint(TERMINAL_PROCESSING_STATUSES)
