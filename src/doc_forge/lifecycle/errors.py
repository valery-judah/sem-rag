"""Errors raised by lifecycle validation helpers."""

from __future__ import annotations

from parity.lifecycle.status import ProcessingStatus


class LifecycleInvariantError(ValueError):
    """Base class for lifecycle invariant violations."""


class InvalidLifecycleTransitionError(LifecycleInvariantError):
    """Raised when a caller attempts an illegal status transition."""

    def __init__(self, current: ProcessingStatus, new: ProcessingStatus) -> None:
        self.current = current
        self.new = new
        super().__init__(f"cannot transition processing status from {current.value} to {new.value}")
