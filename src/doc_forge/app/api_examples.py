"""Companion module for API payload examples used in OpenAPI schema generation."""

from __future__ import annotations

from typing import Any

RETRIEVAL_QUERY_REQUEST_EXAMPLE: dict[str, Any] = {
    "doc_id": "doc_1234abcd",
    "query": "What are the scalability limits of the new database?",
    "k": 3,
}

QUERY_ANSWER_RESPONSE_EXAMPLE: dict[str, Any] = {
    "query_id": "qry_1234abcd",
    "answer": {
        "answer_text": "Supports up to 10,000 concurrent connections.",
        "visible_limitations": [],
        "should_render_citations": True,
        "grounded_evidence_set_ids": ["es_9876xyz"],
        "generator_version": "v1.0",
    },
    "support_state": "sufficient",
    "answer_mode": "direct_answer",
    "citations": {
        "citations": [
            {
                "evidence_set_id": "es_9876xyz",
                "source_reference": {
                    "doc_id": "doc_1234abcd",
                    "document_title": "Database Architecture",
                    "snippet": "Supports up to 10,000 concurrent connections.",
                    "section_id": "sec_1",
                    "heading_path": ["Scalability"],
                    "page_label": "42",
                    "chunk_id": "chk_5678",
                    "passage_anchor": None,
                },
                "support_role": "primary",
            }
        ],
        "material_doc_ids": ["doc_1234abcd"],
        "renderer_version": "v1.0",
    },
    "message": "query answer completed with grounded generation and rendered citations",
}

WORKER_JOB_RESULT_EXAMPLE: dict[str, Any] = {
    "job_id": "job_9876xyz",
    "status": "completed",
}

ERROR_RESPONSE_EXAMPLE: dict[str, Any] = {
    "detail": "The requested document was not found.",
}

SYSTEM_STATUS_RESPONSE_EXAMPLE: dict[str, Any] = {
    "status": "ok",
}

DOCUMENT_DETAIL_RESPONSE_EXAMPLE: dict[str, Any] = {
    "doc_id": "doc_1234abcd",
    "workspace_id": "workspace_alpha",
    "source_type": "pdf",
    "title": "Database Architecture Design",
    "filename": "database_architecture.pdf",
    "uploaded_at": "2024-03-10T15:30:00Z",
    "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "ingest_status": "completed",
    "failure_code": None,
    "failure_detail": None,
    "raw_storage_path": "workspaces/workspace_alpha/documents/doc_1234abcd/raw.pdf",
}

HEALTHZ_ENDPOINT_DESCRIPTION: str = (
    "Lightweight liveness probe that indicates whether the application process is running."
)

READYZ_ENDPOINT_DESCRIPTION: str = (
    "Deep readiness probe that validates connections to the database, "
    "vector store, and artifact storage."
)
