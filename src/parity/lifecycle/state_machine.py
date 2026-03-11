"""Lifecycle transition rules and validation helpers."""

from __future__ import annotations

from parity.lifecycle.errors import InvalidLifecycleTransitionError
from parity.lifecycle.status import ProcessingStatus

_LINEAR_TRANSITIONS: dict[ProcessingStatus, frozenset[ProcessingStatus]] = {
    ProcessingStatus.UPLOADED: frozenset({ProcessingStatus.REGISTERED}),
    ProcessingStatus.REGISTERED: frozenset({ProcessingStatus.EXTRACTING, ProcessingStatus.FAILED}),
    ProcessingStatus.EXTRACTING: frozenset({ProcessingStatus.NORMALIZED, ProcessingStatus.FAILED}),
    ProcessingStatus.NORMALIZED: frozenset({ProcessingStatus.CHUNKED, ProcessingStatus.FAILED}),
    ProcessingStatus.CHUNKED: frozenset({ProcessingStatus.INDEXED, ProcessingStatus.FAILED}),
    ProcessingStatus.INDEXED: frozenset({ProcessingStatus.READY, ProcessingStatus.FAILED}),
    ProcessingStatus.READY: frozenset(),
    ProcessingStatus.FAILED: frozenset(),
}


def allowed_next_processing_statuses(
    current: ProcessingStatus,
) -> frozenset[ProcessingStatus]:
    """Return the legal next statuses for the given current status."""

    return _LINEAR_TRANSITIONS[current]


def can_transition_processing_status(
    current: ProcessingStatus,
    new: ProcessingStatus,
) -> bool:
    """Return whether a transition is allowed by the locked Phase 1 lifecycle."""

    return new in allowed_next_processing_statuses(current)


def require_processing_status_transition(
    current: ProcessingStatus,
    new: ProcessingStatus,
) -> None:
    """Raise when a transition falls outside the locked lifecycle."""

    if not can_transition_processing_status(current, new):
        raise InvalidLifecycleTransitionError(current, new)
