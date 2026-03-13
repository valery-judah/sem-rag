from __future__ import annotations

from datetime import UTC, datetime

from doc_forge.corpus import SourceReference
from doc_forge.evaluation import AnswerLayerCitation
from doc_forge.evaluation.identifiers import parse_corpus_id
from doc_forge.identifiers import parse_doc_id
from doc_forge.query import (
    AnswerDraft,
    AnswerMode,
    CitationBundle,
    CitationRecord,
    CitationSupportRole,
    QueryRunStatus,
    SupportState,
)
from doc_forge.query.review import (
    QueryCitationReview,
    QueryRunReviewSummary,
    QueryTraceReview,
    QueryTraceTimingSummary,
)
from doc_forge.query.trace import QueryTraceBundle
from e2e.eval_support import _parse_page_label, runtime_query_to_answer_layer_input
from e2e.query_support import ExecutedQueryRun
from e2e.support import QueryAnswerResponse


def test_parse_page_label_handles_single_and_range_forms() -> None:
    assert _parse_page_label("p. 3") == (3, None)
    assert _parse_page_label("pp. 8-10") == (8, 10)
    assert _parse_page_label("appendix") == (None, None)
    assert _parse_page_label(None) == (None, None)


def test_runtime_query_to_answer_layer_input_remaps_runtime_doc_ids() -> None:
    submitted_at = datetime(2026, 3, 13, tzinfo=UTC)
    executed = ExecutedQueryRun(
        workspace_id="ws-1",
        question="Where is the latency target defined?",
        response=QueryAnswerResponse(
            query_id="qry-1",
            answer=AnswerDraft(
                answer_text="under 2.5 seconds median end-to-end latency",
                grounded_evidence_set_ids=["es-1"],
                generator_version="answer_generation.deterministic.v1",
            ),
            support_state=SupportState.SUFFICIENT,
            answer_mode=AnswerMode.DIRECT_ANSWER,
            citations=CitationBundle(
                citations=[
                    CitationRecord(
                        evidence_set_id="es-1",
                        support_role=CitationSupportRole.PRIMARY,
                        source_reference=SourceReference(
                            doc_id="doc-runtime-1",
                            document_title="Research Notes 1",
                            snippet=(
                                "The interactive target used in this study was under 2.5 seconds."
                            ),
                            heading_path=["2. Study Context", "2.2 What counts as success"],
                            page_label="p. 2",
                        ),
                    )
                ],
                material_doc_ids=["doc-runtime-1"],
            ),
            message="ok",
        ),
        summary=QueryRunReviewSummary(
            query_id="qry-1",
            workspace_id="ws-1",
            question="Where is the latency target defined?",
            status=QueryRunStatus.SUCCEEDED,
            submitted_at=submitted_at,
            policy_snapshot={},
            trace_summary=QueryTraceTimingSummary(trace_count=0, stages=[]),
            has_answer=True,
        ),
        trace=QueryTraceReview(
            summary=QueryRunReviewSummary(
                query_id="qry-1",
                workspace_id="ws-1",
                question="Where is the latency target defined?",
                status=QueryRunStatus.SUCCEEDED,
                submitted_at=submitted_at,
                policy_snapshot={},
                trace_summary=QueryTraceTimingSummary(trace_count=0, stages=[]),
                has_answer=True,
            ),
            trace_bundle=QueryTraceBundle(query_id="qry-1", run_status=QueryRunStatus.SUCCEEDED),
        ),
        citations_review=QueryCitationReview(
            query_id="qry-1",
            support_state=SupportState.SUFFICIENT,
            answer_mode=AnswerMode.DIRECT_ANSWER,
            citations=CitationBundle(citations=[], material_doc_ids=[]),
        ),
    )

    run_input = runtime_query_to_answer_layer_input(
        case_id="lookup_rn1_001",
        query_run=executed,
        runtime_doc_id_map={parse_doc_id("doc-runtime-1"): parse_corpus_id("research-notes-1")},
    )

    assert run_input.case_id == "lookup_rn1_001"
    assert run_input.answer_text == "under 2.5 seconds median end-to-end latency"
    assert run_input.citations == [
        AnswerLayerCitation(
            doc_id=parse_corpus_id("research-notes-1"),
            document_title="Research Notes 1",
            section_path=["2. Study Context", "2.2 What counts as success"],
            page_start=2,
        )
    ]
