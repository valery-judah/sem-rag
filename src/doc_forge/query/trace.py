"""Structured query trace payloads."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from doc_forge.identifiers import QueryId

from .contracts import QueryRunStatus, QueryStageName


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


class QueryStageTraceStatus(StrEnum):
    """Status for an individual stage trace."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class QueryStageTrace(BaseModel):
    """Structured trace payload for a single query stage."""

    model_config = ConfigDict(extra="forbid")

    query_id: QueryId = Field(min_length=1)
    stage_name: QueryStageName
    stage_status: QueryStageTraceStatus
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    payload: dict[str, object] = Field(default_factory=lambda: {})

    @model_validator(mode="after")
    def validate_finished_at(self) -> QueryStageTrace:
        if self.finished_at is not None and self.finished_at < self.started_at:
            raise ValueError("finished_at must be greater than or equal to started_at")
        return self


class QueryTraceBundle(BaseModel):
    """Run-level trace bundle with ordered stage traces."""

    model_config = ConfigDict(extra="forbid")

    query_id: QueryId = Field(min_length=1)
    run_status: QueryRunStatus
    stage_traces: list[QueryStageTrace] = Field(default_factory=lambda: [])
