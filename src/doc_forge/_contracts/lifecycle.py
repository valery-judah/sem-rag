"""Compatibility exports for lifecycle contracts."""

from __future__ import annotations

from doc_forge.lifecycle import (
    IN_FLIGHT_PROCESSING_STATUSES,
    TERMINAL_PROCESSING_STATUSES,
    ProcessingStatus,
    allowed_next_processing_statuses,
    can_transition_processing_status,
    require_processing_status_transition,
)

__all__ = [
    "IN_FLIGHT_PROCESSING_STATUSES",
    "TERMINAL_PROCESSING_STATUSES",
    "ProcessingStatus",
    "allowed_next_processing_statuses",
    "can_transition_processing_status",
    "require_processing_status_transition",
]
