from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from parity._contracts import SourceReference
from parity.query import (
    AnswerDraft,
    AnswerMode,
    AnswerModeDecision,
    CitationBundle,
    CitationRecord,
    CitationSupportRole,
    ContextItem,
    ContextManifest,
    CorpusSnapshot,
    EvidenceGroupingMode,
    EvidenceSet,
    EvidenceUnit,
    FinalQueryArtifacts,
    InterpretedQuery,
    QueryPolicyOverride,
    QueryRequest,
    QueryRequestType,
    QueryRun,
    QueryRunStatus,
    QuerySpecificity,
    QueryTerminalFailure,
    RetrievedCandidate,
    SupportAssessment,
    SupportQualifierReason,
    SupportState,
    SynthesisMode,
    TrustFailureLabel,
    UnsupportedCapability,
)

pytestmark = pytest.mark.contract


def make_source_reference(**overrides: Any) -> SourceReference:
    return SourceReference(
        doc_id="doc-1",
        document_title="Doc 1",
        snippet="Supporting passage.",
        heading_path=["Chapter 1"],
        chunk_id="chunk-1",
        **overrides,
    )


def make_candidate(**overrides: Any) -> RetrievedCandidate:
    payload: dict[str, Any] = {
        "doc_id": "doc-1",
        "chunk_id": "chunk-1",
        "heading_path": ["Chapter 1"],
        "retrieval_score": 0.9,
        "retrieval_rank": 1,
        "locator": "p. 3",
    }
    payload.update(overrides)
    return RetrievedCandidate(
        **payload,
    )


def test_query_request_requires_question_and_workspace() -> None:
    request = QueryRequest(
        question="What does the document say about vector search?",
        workspace_id="workspace-1",
        policy_overrides=QueryPolicyOverride(retrieval_candidate_cap=10),
    )

    assert request.policy_overrides is not None
    assert request.policy_overrides.retrieval_candidate_cap == 10

    with pytest.raises(ValidationError, match="question"):
        QueryRequest(question="", workspace_id="workspace-1")

    with pytest.raises(ValidationError, match="workspace_id"):
        QueryRequest(question="Valid question", workspace_id="")


def test_query_run_requires_policy_snapshot() -> None:
    run = QueryRun(
        query_id="qry-1",
        workspace_id="workspace-1",
        question="What is semantic retrieval?",
        status=QueryRunStatus.PENDING,
        submitted_at=datetime(2026, 3, 11, tzinfo=UTC),
        policy_snapshot={"retrieval_candidate_cap": 24},
    )

    assert run.query_id == "qry-1"

    with pytest.raises(ValidationError, match="policy_snapshot"):
        QueryRun.model_validate(
            {
                "query_id": "qry-1",
                "workspace_id": "workspace-1",
                "question": "What is semantic retrieval?",
                "policy_snapshot": None,
            }
        )


def test_failed_query_run_requires_terminal_failure_and_completed_at() -> None:
    with pytest.raises(ValidationError, match="completed_at"):
        QueryRun(
            query_id="qry-1",
            workspace_id="workspace-1",
            question="What is semantic retrieval?",
            status=QueryRunStatus.FAILED,
            submitted_at=datetime(2026, 3, 11, tzinfo=UTC),
            policy_snapshot={"retrieval_candidate_cap": 24},
            terminal_failure=QueryTerminalFailure(
                error_code="query_execution_failed",
                error_class="RuntimeError",
                message="failed",
            ),
        )


def test_corpus_snapshot_allows_empty_doc_set() -> None:
    snapshot = CorpusSnapshot(
        workspace_id="workspace-1",
        query_started_at=datetime(2026, 3, 11, tzinfo=UTC),
        eligible_doc_ids=[],
    )

    assert snapshot.eligible_doc_ids == []


def test_interpreted_query_preserves_shape_flags() -> None:
    interpreted = InterpretedQuery(
        normalized_question="what is semantic retrieval",
        request_type=QueryRequestType.EXPLANATION,
        answer_shape="explanatory paragraph",
        specificity=QuerySpecificity.PRECISE,
        scope_hints=["retrieval", "embeddings"],
        requires_synthesis=False,
        synthesis_mode=SynthesisMode.NONE,
        requires_source_navigation=True,
        unsupported_capability_flags=[],
        normalization_notes=["lowercased"],
    )

    assert interpreted.request_type is QueryRequestType.EXPLANATION
    assert interpreted.requires_source_navigation is True
    assert interpreted.specificity is QuerySpecificity.PRECISE


def test_interpreted_query_preserves_unsupported_capability_flags() -> None:
    interpreted = InterpretedQuery(
        normalized_question="analyze the figure on page 3",
        request_type=QueryRequestType.UNSUPPORTED,
        answer_shape="capability boundary response",
        specificity=QuerySpecificity.SECTION_SCOPED,
        requires_synthesis=False,
        synthesis_mode=SynthesisMode.NONE,
        requires_source_navigation=False,
        unsupported_capability_flags=[UnsupportedCapability.IMAGE_OR_FIGURE_REASONING],
        normalization_notes=[],
    )

    assert interpreted.unsupported_capability_flags == [
        UnsupportedCapability.IMAGE_OR_FIGURE_REASONING
    ]


def test_retrieved_candidate_requires_rank_and_heading_path() -> None:
    candidate = make_candidate()

    assert candidate.retrieval_rank == 1

    with pytest.raises(ValidationError, match="retrieval_rank"):
        make_candidate(retrieval_rank=0)

    with pytest.raises(ValidationError, match="heading_path"):
        make_candidate(heading_path=[])


def test_evidence_set_requires_evidence_units() -> None:
    evidence_set = EvidenceSet(
        evidence_set_id="es-1",
        grouping_mode=EvidenceGroupingMode.SINGLE_PASSAGE,
        evidence_units=[
            EvidenceUnit(
                evidence_unit_id="eu-1",
                candidate=make_candidate(),
                source_reference=make_source_reference(),
                unit_rank=1,
                selection_reason="Selected as direct evidence.",
            )
        ],
        purpose="direct_support",
        coverage_notes=["Single passage directly answers the question."],
        conflict_flags=[],
        assembly_reason="Single passage directly answers the question.",
    )

    assert evidence_set.grouping_mode is EvidenceGroupingMode.SINGLE_PASSAGE

    with pytest.raises(ValidationError, match="evidence_units"):
        EvidenceSet(
            evidence_set_id="es-1",
            grouping_mode=EvidenceGroupingMode.SINGLE_PASSAGE,
            evidence_units=[],
            purpose="direct_support",
            coverage_notes=[],
            conflict_flags=[],
            assembly_reason="Invalid empty set.",
        )


def test_context_manifest_rejects_budget_overflow() -> None:
    manifest = ContextManifest(
        ordered_evidence_set_ids=["es-1"],
        included_evidence_set_ids=["es-1"],
        inclusion_reasons={"es-1": "included_within_budget"},
        token_budget=4000,
        token_budget_used=512,
        context_items=[
            ContextItem(
                evidence_set_id="es-1",
                assembly_rank=1,
                rendered_text="Doc 1 | direct_support | Chapter 1\n[p. 3] Supporting passage.",
                contributing_doc_ids=["doc-1"],
                heading_paths=[["Chapter 1"]],
                locators=["p. 3"],
                estimated_token_count=16,
            )
        ],
    )

    assert manifest.token_budget_used == 512

    with pytest.raises(ValidationError, match="token_budget_used must not exceed token_budget"):
        ContextManifest(
            ordered_evidence_set_ids=["es-1"],
            included_evidence_set_ids=["es-1"],
            inclusion_reasons={"es-1": "included_within_budget"},
            token_budget=100,
            token_budget_used=101,
            context_items=[
                ContextItem(
                    evidence_set_id="es-1",
                    assembly_rank=1,
                    rendered_text="Doc 1 | direct_support | Chapter 1\n[p. 3] Supporting passage.",
                    contributing_doc_ids=["doc-1"],
                    heading_paths=[["Chapter 1"]],
                    locators=["p. 3"],
                    estimated_token_count=16,
                )
            ],
        )


def test_context_manifest_requires_context_items_to_match_included_ids() -> None:
    with pytest.raises(
        ValidationError,
        match="context_items must align to included_evidence_set_ids in order",
    ):
        ContextManifest(
            ordered_evidence_set_ids=["es-1"],
            included_evidence_set_ids=["es-2"],
            dropped_evidence_set_ids=["es-1"],
            inclusion_reasons={"es-2": "included_within_budget"},
            exclusion_reasons={"es-1": "dropped_over_budget"},
            token_budget=100,
            token_budget_used=16,
            context_items=[
                ContextItem(
                    evidence_set_id="es-1",
                    assembly_rank=1,
                    rendered_text="Doc 1 | direct_support | Chapter 1\n[p. 3] Supporting passage.",
                    contributing_doc_ids=["doc-1"],
                    heading_paths=[["Chapter 1"]],
                    locators=["p. 3"],
                    estimated_token_count=16,
                )
            ],
        )


def test_support_assessment_and_answer_decision_round_trip() -> None:
    assessment = SupportAssessment(
        support_state=SupportState.PARTIAL,
        qualifying_reason_codes=[
            SupportQualifierReason.MISSING_MATERIAL_COVERAGE,
            SupportQualifierReason.SCOPE_NARROWING_REQUIRED,
        ],
        trust_failure_labels=[TrustFailureLabel.U2],
        unsupported_gaps=["The corpus does not fully cover the requested scope."],
    )
    decision = AnswerModeDecision(
        answer_mode=AnswerMode.QUALIFIED_ANSWER,
        rationale="Partial support requires visible qualification.",
        based_on_support_state=assessment.support_state,
        required_qualifying_reason_codes=[SupportQualifierReason.SCOPE_NARROWING_REQUIRED],
        allowed_scope_summary="Only the supported portion may be answered.",
    )
    draft = AnswerDraft(
        answer_text="The corpus partially addresses the question.",
        visible_limitations=["The answer is qualified because support is partial."],
        grounded_evidence_set_ids=["es-1"],
        generator_version="answer_generation.deterministic.v1",
    )
    citations = CitationBundle(
        citations=[
            CitationRecord(
                evidence_set_id="es-1",
                source_reference=make_source_reference(),
                support_role=CitationSupportRole.PRIMARY,
            )
        ],
        material_doc_ids=["doc-1"],
        renderer_version="citation_rendering.deterministic.v1",
    )
    artifacts = FinalQueryArtifacts(
        answer=draft,
        citations=citations,
        support_state=assessment.support_state,
        qualifying_reason_codes=assessment.qualifying_reason_codes,
        answer_mode=decision.answer_mode,
        trust_failure_labels=assessment.trust_failure_labels,
    )

    assert decision.based_on_support_state is SupportState.PARTIAL
    assert assessment.qualifying_reason_codes == [
        SupportQualifierReason.MISSING_MATERIAL_COVERAGE,
        SupportQualifierReason.SCOPE_NARROWING_REQUIRED,
    ]
    assert draft.should_render_citations is True
    assert artifacts.citations.material_doc_ids == ["doc-1"]
