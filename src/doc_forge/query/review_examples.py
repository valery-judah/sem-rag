"""Companion module for query review payload examples used in OpenAPI schema generation."""

from __future__ import annotations

from typing import Any

QUERY_RUN_REVIEW_SUMMARY_EXAMPLE: dict[str, Any] = {
    "query_id": "qry_1234abcd",
    "workspace_id": "workspace_alpha",
    "question": "What are the scalability limits of the new database?",
    "status": "succeeded",
    "submitted_at": "2024-03-10T15:30:00Z",
    "completed_at": "2024-03-10T15:30:05Z",
    "policy_snapshot": {"retrieval_candidate_cap": 20},
    "snapshot_summary": {
        "workspace_id": "workspace_alpha",
        "query_started_at": "2024-03-10T15:30:00Z",
        "eligible_doc_ids": ["doc_1234abcd"],
        "retrieval_index_version": "v2",
        "readiness_version": "v1.1",
    },
    "support_state": "sufficient",
    "answer_mode": "direct_answer",
    "trust_failure_labels": [],
    "visible_limitations": [],
    "has_answer": True,
    "terminal_failure": None,
    "trace_summary": {
        "trace_count": 1,
        "total_duration_ms": 1000,
        "stages": [
            {
                "stage_name": "retrieve",
                "stage_status": "succeeded",
                "started_at": "2024-03-10T15:30:01Z",
                "finished_at": "2024-03-10T15:30:02Z",
                "duration_ms": 1000,
            }
        ],
    },
}

QUERY_TRACE_REVIEW_EXAMPLE: dict[str, Any] = {
    "summary": QUERY_RUN_REVIEW_SUMMARY_EXAMPLE,
    "snapshot": {
        "workspace_id": "workspace_alpha",
        "query_started_at": "2024-03-10T15:30:00Z",
        "eligible_doc_ids": ["doc_1234abcd"],
        "retrieval_index_version": "v2",
        "readiness_version": "v1.1",
    },
    "trace_bundle": {
        "query_id": "qry_1234abcd",
        "run_status": "succeeded",
        "stage_traces": [
            {
                "stage_name": "retrieve",
                "stage_status": "succeeded",
                "started_at": "2024-03-10T15:30:01Z",
                "finished_at": "2024-03-10T15:30:02Z",
                "payload": {"candidate_count": 5},
                "error": None,
            }
        ],
    },
    "final_artifacts": {
        "answer": {
            "answer_text": "Supports up to 10,000 concurrent connections.",
            "visible_limitations": [],
            "should_render_citations": True,
            "grounded_evidence_set_ids": ["es_9876xyz"],
            "generator_version": "v1.0",
        },
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
        "support_state": "sufficient",
        "qualifying_reason_codes": [],
        "answer_mode": "direct_answer",
        "trust_failure_labels": [],
        "created_at": "2024-03-10T15:30:05Z",
    },
}

QUERY_CITATION_REVIEW_EXAMPLE: dict[str, Any] = {
    "query_id": "qry_1234abcd",
    "support_state": "sufficient",
    "answer_mode": "direct_answer",
    "trust_failure_labels": [],
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
}
