"""Internal lifecycle runtime types and helpers."""

from doc_forge.lifecycle.errors import InvalidLifecycleTransitionError, LifecycleInvariantError
from doc_forge.lifecycle.models import FailureCategory, LifecycleEvent, LifecycleStage
from doc_forge.lifecycle.state_machine import (
    allowed_next_processing_statuses,
    can_transition_processing_status,
    require_processing_status_transition,
)
from doc_forge.lifecycle.status import (
    IN_FLIGHT_PROCESSING_STATUSES,
    TERMINAL_PROCESSING_STATUSES,
    ProcessingStatus,
)

__all__ = [
    "FailureCategory",
    "IN_FLIGHT_PROCESSING_STATUSES",
    "InvalidLifecycleTransitionError",
    "LifecycleEvent",
    "LifecycleInvariantError",
    "LifecycleStage",
    "ProcessingStatus",
    "TERMINAL_PROCESSING_STATUSES",
    "allowed_next_processing_statuses",
    "can_transition_processing_status",
    "require_processing_status_transition",
]
