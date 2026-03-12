"""Shared base types for lifecycle stage runners."""

from __future__ import annotations

from typing import Protocol

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


class StageRunner(Protocol):
    """Executable lifecycle stage bound to one queued job target."""

    target_stage: DocumentJobStage

    def run(self, job: DocumentJob) -> DocumentJobStage | None:
        """Run the stage and return the next queued stage, if any."""
