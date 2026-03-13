---
artifact_kind: workstream
id: WS-018
title: Structured Logging
work_type: feature
status: active
owner:
created: 2026-03-13
updated: 2026-03-13
---

# Summary
Bring type safety, discoverability, and structural integrity to the currently unstructured `dict[str, Any]` log events emitted via `structlog`.

## Objective
Introduce a strongly-typed event taxonomy, structural typing for standard contexts, domain-specific facades, and runtime schema validation for audit-critical logs to make the observability system robust, type-safe, and highly testable.

## Non-goals
- Refactoring every single debug/trace log line across the application.
- Enforcing heavy runtime validation (e.g., Pydantic) on high-throughput, non-critical logs.
- Replacing the underlying `structlog` engine with a different library.

## Current status
- The project currently enforces structured JSON logging via `structlog`.
- However, event dictionaries are passed around and captured dynamically as `dict[str, Any]`.
- Developers rely heavily on "magic strings" for event names, leading to potential typos.
- The `StructuredLogCapture` test fixture validates log presence but cannot assert strict structural schemas or contracts for log payloads.

## Next step
- Define the initial `StrEnum` for core log events and implement the first domain-specific logger facade (e.g., `WorkerLogger`).

## Relevant context
- **paths:** `tests/conftest.py`, `src/doc_forge/app/logging.py`
- **components:** `structlog`, `StructuredLogCapture`, `pytest`
- **constraints:** Must maintain the performance characteristics of standard Python logging while adding type safety.
- **read first:** `docs/conventions/python-logging.md`

## Workflow steps

1. **Event Taxonomy (Standardization Pattern):** Define a centralized `StrEnum` (e.g., `LogEvent`) for all log event names to prevent magic string typos and provide a single source of truth.
   ```python
   from enum import StrEnum

   class LogEvent(StrEnum):
       WORKER_JOB_CLAIMED = "worker.job.claimed"
       WORKER_JOB_FAILED = "worker.job.failed"
       DOCUMENT_UPLOAD_REGISTERED = "document.upload.registered"
   ```

2. **Context Typing (Structural Typing):** Create `TypedDict` definitions for standard logging contexts (e.g., `WorkerLogContext`, `RequestContext`) to enable structural type hinting for `.bind()`.
   ```python
   from typing import TypedDict, NotRequired

   class WorkerLogContext(TypedDict):
       worker_id: str
       queue_name: str
       attempt_count: NotRequired[int]

   # Usage
   logger = get_logger().bind(**WorkerLogContext(worker_id="w-1", queue_name="default"))
   ```

3. **Logger Facades (Adapter Pattern):** Implement Domain-Specific Logger Facades (e.g., `WorkerLogger`) that wrap the raw `structlog` logger to provide strongly-typed method signatures for critical domain logging. This fixes the issue of `logger.info(msg, **kwargs)` defeating `mypy`.
   ```python
   from doc_forge.identifiers import DocId

   class WorkerLogger:
       def __init__(self, logger: structlog.stdlib.BoundLogger):
           self._logger = logger
           
       def job_claimed(self, doc_id: DocId, job_id: str, target_stage: str, status: str) -> None:
           self._logger.info(
               LogEvent.WORKER_JOB_CLAIMED, 
               doc_id=doc_id, 
               job_id=job_id, 
               target_stage=target_stage, 
               status=status
           )
   ```

4. **Audit Validation (Validation Pattern):** Define explicit Pydantic `BaseModel` schemas for audit-critical logs that require strict runtime validation before downstream ingestion.
   ```python
   class DocumentRegisteredAuditLog(BaseModel):
       workspace_id: str
       doc_id: DocId
       source_type: SourceType
       duration_ms: int

   # Usage
   audit_data = DocumentRegisteredAuditLog(workspace_id=ws, doc_id=id, source_type=st, duration_ms=ms)
   logger.info(LogEvent.DOCUMENT_UPLOAD_REGISTERED, **audit_data.model_dump())
   ```

5. **Contract Testing:** Upgrade the `StructuredLogCapture` test fixture in `tests/conftest.py` to assert that emitted logs correctly match the newly defined `TypedDict` schemas or Pydantic models.
   ```python
       def assert_event_matches(self, event_name: LogEvent, schema: type[BaseModel]) -> None:
           raw_event = self._find_raw_event(event_name) # returns dict[str, Any]
           schema.model_validate(raw_event) # raises error if log is malformed
   ```

## Validation
- The `uv run poe type` (mypy) checks must pass with the new strictly-typed facades and enums.
- The existing test suite must pass successfully.
- Tests leveraging `structured_caplog` must successfully utilize the newly upgraded schema assertions.

## Linked artifacts
- `docs/conventions/python-logging.md`