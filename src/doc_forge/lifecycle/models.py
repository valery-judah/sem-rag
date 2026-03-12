"""Internal runtime models for document lifecycle execution."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from doc_forge.lifecycle.status import ProcessingStatus


class LifecycleStage(StrEnum):
    """Named lifecycle stages used by the runtime and event log."""

    UPLOAD = "upload"
    REGISTER = "register"
    EXTRACT = "extract"
    NORMALIZE = "normalize"
    CHUNK = "chunk"
    INDEX = "index"
    READINESS = "readiness"


class FailureCategory(StrEnum):
    """Small failure taxonomy for lifecycle events."""

    VALIDATION = "validation"
    UNSUPPORTED_INPUT = "unsupported_input"
    PROCESSING = "processing"
    INTERNAL = "internal"


class LifecycleEvent(BaseModel):
    """Storage-independent lifecycle transition record."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    doc_id: str
    stage: LifecycleStage
    from_status: ProcessingStatus | None = None
    to_status: ProcessingStatus
    occurred_at: datetime
    failure_category: FailureCategory | None = None
    detail: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_failure_fields(self) -> LifecycleEvent:
        is_failure = self.to_status is ProcessingStatus.FAILED

        if is_failure and self.failure_category is None:
            raise ValueError("failed lifecycle events must include a failure_category")
        if not is_failure and self.failure_category is not None:
            raise ValueError("non-failed lifecycle events must not include a failure_category")

        return self
