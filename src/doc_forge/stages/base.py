"""Shared base types for lifecycle stage runners."""

from __future__ import annotations

from typing import Any, Protocol

import structlog

from doc_forge.app.log_events import LogEvent
from doc_forge.identifiers import DocId
from doc_forge.lifecycle import FailureCategory
from doc_forge.persistence import DocumentJob, DocumentJobStage


class StageExecutionError(RuntimeError):
    """Raised when a stage fails with an attributable lifecycle error."""

    def __init__(
        self,
        *,
        error_code: str,
        error_detail: str,
        failure_category: FailureCategory = FailureCategory.PROCESSING,
    ) -> None:
        self.error_code = error_code
        self.error_detail = error_detail
        self.failure_category = failure_category
        super().__init__(error_detail)


class StageLogger:
    """Standardized logger facade for all document lifecycle stages."""

    def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
        self._logger = logger

    def stage_started(self, stage_name: str, doc_id: DocId, job_id: str | None) -> None:
        self._logger.info(
            LogEvent.LIFECYCLE_STAGE_STARTED,
            stage_name=stage_name,
            doc_id=doc_id,
            job_id=job_id,
        )

    def stage_failed(
        self,
        stage_name: str,
        doc_id: DocId,
        job_id: str | None,
        duration_ms: int,
        error_code: str | None = None,
        **extra: Any,
    ) -> None:
        self._logger.warning(
            LogEvent.LIFECYCLE_STAGE_FAILED,
            stage_name=stage_name,
            doc_id=doc_id,
            job_id=job_id,
            duration_ms=duration_ms,
            error_code=error_code,
            **extra,
        )

    def stage_completed(
        self, stage_name: str, doc_id: DocId, job_id: str | None, duration_ms: int, **extra: Any
    ) -> None:
        self._logger.info(
            LogEvent.LIFECYCLE_STAGE_COMPLETED,
            stage_name=stage_name,
            doc_id=doc_id,
            job_id=job_id,
            duration_ms=duration_ms,
            **extra,
        )


class StageRunner(Protocol):
    """Executable lifecycle stage bound to one queued job target."""

    target_stage: DocumentJobStage

    def run(self, job: DocumentJob) -> DocumentJobStage | None:
        """Run the stage and return the next queued stage, if any."""
