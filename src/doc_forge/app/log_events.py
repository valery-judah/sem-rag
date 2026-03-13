from enum import StrEnum


class LogEvent(StrEnum):
    # Worker
    WORKER_RUN_NEXT_INVOKED = "worker.run_next.invoked"
    WORKER_RUN_NEXT_IDLE = "worker.run_next.idle"
    WORKER_JOB_CLAIMED = "worker.job.claimed"
    WORKER_JOB_STARTED = "worker.job.started"
    WORKER_JOB_SUCCEEDED = "worker.job.succeeded"
    WORKER_JOB_FAILED = "worker.job.failed"

    # Orchestrator
    WORKER_JOB_ENQUEUE_SKIPPED = "worker.job.enqueue_skipped"
    WORKER_JOB_ENQUEUED = "worker.job.enqueued"

    # Document Lifecycle Service
    DOCUMENT_UPLOAD_VALIDATED = "document.upload.validated"
    DOCUMENT_UPLOAD_REGISTERED = "document.upload.registered"
    DOCUMENT_DELETE_PERFORMED = "document.delete.performed"
    DOCUMENT_RETRY_ELIGIBILITY_CHECKED = "document.retry.eligibility_checked"
    DOCUMENT_RETRY_ELIGIBILITY_REJECTED = "document.retry.eligibility_rejected"
    DOCUMENT_RETRY_QUEUED_INTERNAL = "document.retry.queued_internal"
    RETRIEVAL_SMOKE_EXECUTED = "retrieval.smoke.executed"

    # Stages
    LIFECYCLE_STAGE_STARTED = "lifecycle.stage.started"
    LIFECYCLE_STAGE_FAILED = "lifecycle.stage.failed"
    LIFECYCLE_STAGE_COMPLETED = "lifecycle.stage.completed"

    # Embeddings
    EMBEDDING_MODEL_GENERATED = "embedding.model.generated"

    # Query Service
    QUERY_RUN_STARTED = "query.run.started"
    QUERY_STAGE_STARTED = "query.stage.started"
    QUERY_STAGE_COMPLETED = "query.stage.completed"
    QUERY_RUN_COMPLETED = "query.run.completed"
    QUERY_RUN_FAILED = "query.run.failed"

    # Answer Generation
    QUERY_LLM_GENERATED = "query.llm.generated"

    # Query Review
    REVIEW_QUERY_LOADED = "review.query.loaded"
    REVIEW_TRACE_LOADED = "review.trace.loaded"
    REVIEW_CITATIONS_LOADED = "review.citations.loaded"

    # Query Replay
    REPLAY_BUNDLE_BUILT = "replay.bundle.built"
