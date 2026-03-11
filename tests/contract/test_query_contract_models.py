from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from parity._contracts import SourceReference
from parity.query import (
    AnswerDraft,
    AnswerMode,
    AnswerModeDecision,
    ContextManifest,
    CorpusSnapshot,
    EvidenceGroupingMode,
    EvidenceSet,
    EvidenceUnit,
    InterpretedQuery,
    QueryPolicyOverride,
    QueryRequest,
    QueryRequestType,
    QueryRun,
    QueryRunStatus,
    QuerySpecificity,
    RetrievedCandidate,
    SupportAssessment,
    SupportState,
    SynthesisMode,
    TrustFailureLabel,
    UnsupportedCapability,
)

pytestmark = pytest.mark.contract


def make_source_reference(**overrides: object) -> SourceReference:
    return SourceReference(
        doc_id="doc-1",
        document_title="Doc 1",
        snippet="Supporting passage.",
        heading_path=["Chapter 1"],
        chunk_id="chunk-1",
        **overrides,
    )


def make_candidate(**overrides: object) -> RetrievedCandidate:
    payload: dict[str, object] = {
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
        QueryRun(
            query_id="qry-1",
            workspace_id="workspace-1",
            question="What is semantic retrieval?",
            policy_snapshot=None,
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
            )
        ],
        rationale="Single passage directly answers the question.",
    )

    assert evidence_set.grouping_mode is EvidenceGroupingMode.SINGLE_PASSAGE

    with pytest.raises(ValidationError, match="evidence_units"):
        EvidenceSet(
            evidence_set_id="es-1",
            grouping_mode=EvidenceGroupingMode.SINGLE_PASSAGE,
            evidence_units=[],
            rationale="Invalid empty set.",
        )


def test_context_manifest_rejects_budget_overflow() -> None:
    manifest = ContextManifest(
        ordered_evidence_set_ids=["es-1"],
        token_budget=4000,
        token_budget_used=512,
    )

    assert manifest.token_budget_used == 512

    with pytest.raises(ValidationError, match="token_budget_used must not exceed token_budget"):
        ContextManifest(
            ordered_evidence_set_ids=["es-1"],
            token_budget=100,
            token_budget_used=101,
        )


def test_support_assessment_and_answer_decision_round_trip() -> None:
    assessment = SupportAssessment(
        support_state=SupportState.PARTIAL,
        qualifying_reasons=["Evidence answers part of the question but not all of it."],
        trust_failure_labels=[TrustFailureLabel.U2],
    )
    decision = AnswerModeDecision(
        answer_mode=AnswerMode.QUALIFIED_ANSWER,
        rationale="Partial support requires visible qualification.",
        based_on_support_state=assessment.support_state,
    )
    draft = AnswerDraft(
        answer_text="The corpus partially addresses the question.",
        visible_limitations=["The answer is qualified because support is partial."],
    )

    assert decision.based_on_support_state is SupportState.PARTIAL
    assert draft.should_render_citations is True
