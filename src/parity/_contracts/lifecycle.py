"""Lifecycle contracts for document processing."""

from __future__ import annotations

from enum import StrEnum


class ProcessingStatus(StrEnum):
    """Locked processing states for the Phase 1 contract layer."""

    UPLOADED = "uploaded"
    REGISTERED = "registered"
    EXTRACTING = "extracting"
    NORMALIZED = "normalized"
    CHUNKED = "chunked"
    INDEXED = "indexed"
    READY = "ready"
    FAILED = "failed"


_LINEAR_TRANSITIONS: dict[ProcessingStatus, set[ProcessingStatus]] = {
    ProcessingStatus.UPLOADED: {ProcessingStatus.REGISTERED, ProcessingStatus.FAILED},
    ProcessingStatus.REGISTERED: {ProcessingStatus.EXTRACTING, ProcessingStatus.FAILED},
    ProcessingStatus.EXTRACTING: {ProcessingStatus.NORMALIZED, ProcessingStatus.FAILED},
    ProcessingStatus.NORMALIZED: {ProcessingStatus.CHUNKED, ProcessingStatus.FAILED},
    ProcessingStatus.CHUNKED: {ProcessingStatus.INDEXED, ProcessingStatus.FAILED},
    ProcessingStatus.INDEXED: {ProcessingStatus.READY, ProcessingStatus.FAILED},
    ProcessingStatus.READY: set(),
    ProcessingStatus.FAILED: set(),
}


def can_transition_processing_status(
    current: ProcessingStatus,
    new: ProcessingStatus,
) -> bool:
    """Return whether a transition is allowed by the locked Phase 1 lifecycle."""

    return new in _LINEAR_TRANSITIONS[current]
