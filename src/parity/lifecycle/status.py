"""Canonical lifecycle statuses for internal document processing."""

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


IN_FLIGHT_PROCESSING_STATUSES = frozenset(
    {
        ProcessingStatus.REGISTERED,
        ProcessingStatus.EXTRACTING,
        ProcessingStatus.NORMALIZED,
        ProcessingStatus.CHUNKED,
        ProcessingStatus.INDEXED,
    }
)


TERMINAL_PROCESSING_STATUSES = frozenset(
    {
        ProcessingStatus.READY,
        ProcessingStatus.FAILED,
    }
)
