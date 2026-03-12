from __future__ import annotations

from doc_forge._contracts import SourceReference
from doc_forge.query import (
    AnswerMode,
    ContextItem,
    ContextManifest,
    CorpusSnapshot,
    EvidenceGroupingMode,
    EvidenceSet,
    EvidenceUnit,
    InterpretedQuery,
    QueryRequest,
    QueryRequestType,
    QuerySpecificity,
    RetrievedCandidate,
    SupportQualifierReason,
    SupportState,
    SynthesisMode,
    UnsupportedCapability,
)
from doc_forge.query.answer_mode_policy import DeterministicAnswerModePolicy
from doc_forge.query.policies import QueryPolicyDefaults
from doc_forge.query.support_assessment import HybridSupportAssessor


def _candidate(**overrides: object) -> RetrievedCandidate:
    return RetrievedCandidate(
        doc_id="doc-1",
        chunk_id="chunk-1",
        heading_path=["Chapter 1"],
        locator="p. 3",
        retrieval_score=0.9,
        retrieval_rank=1,
    ).model_copy(update=overrides)


def _evidence_set(
    *,
    doc_id: str = "doc-1",
    chunk_id: str = "chunk-1",
    locator: str | None = "p. 3",
    heading_path: list[str] | None = None,
    conflict_flags: list[str] | None = None,
    evidence_set_id: str = "es-1",
) -> EvidenceSet:
    return EvidenceSet(
        evidence_set_id=evidence_set_id,
        grouping_mode=EvidenceGroupingMode.SINGLE_PASSAGE,
        evidence_units=[
            EvidenceUnit(
                evidence_unit_id=f"{evidence_set_id}-unit-1",
                candidate=_candidate(
                    doc_id=doc_id,
                    chunk_id=chunk_id,
                    locator=locator,
                    heading_path=heading_path or ["Chapter 1"],
                ),
                source_reference=SourceReference(
                    doc_id=doc_id,
                    document_title=f"Doc {doc_id}",
                    snippet="Supporting passage.",
                    heading_path=heading_path or ["Chapter 1"],
                    page_label=locator,
                    chunk_id=chunk_id,
                ),
                unit_rank=1,
                selection_reason="Selected as direct support.",
            )
        ],
        purpose="direct_support",
        coverage_notes=[],
        conflict_flags=conflict_flags or [],
        assembly_reason="Supports the request.",
    )


def _manifest(
    *,
    evidence_set_id: str = "es-1",
    doc_id: str = "doc-1",
    locator: str | None = "p. 3",
    heading_paths: list[list[str]] | None = None,
) -> ContextManifest:
    return ContextManifest(
        ordered_evidence_set_ids=[evidence_set_id],
        included_evidence_set_ids=[evidence_set_id],
        dropped_evidence_set_ids=[],
        inclusion_reasons={evidence_set_id: "included_within_budget"},
        exclusion_reasons={},
        token_budget=4000,
        token_budget_used=24,
        context_items=[
            ContextItem(
                evidence_set_id=evidence_set_id,
                assembly_rank=1,
                rendered_text="Doc 1 | direct_support | Chapter 1\n[p. 3] Supporting passage.",
                contributing_doc_ids=[doc_id],
                heading_paths=heading_paths or [["Chapter 1"]],
                locators=[] if locator is None else [locator],
                estimated_token_count=24,
            )
        ],
    )


def _interpreted_query(**overrides: object) -> InterpretedQuery:
    return InterpretedQuery(
        normalized_question="what uses embeddings",
        request_type=QueryRequestType.FACT_LOOKUP,
        answer_shape="direct_answer",
        specificity=QuerySpecificity.PRECISE,
        scope_hints=["embeddings"],
        requires_synthesis=False,
        synthesis_mode=SynthesisMode.NONE,
        requires_source_navigation=False,
        unsupported_capability_flags=[],
        normalization_notes=[],
    ).model_copy(update=overrides)


def test_support_assessment_marks_unsupported_question_type_as_insufficient() -> None:
    assessor = HybridSupportAssessor()
    result = assessor.assess(
        request=QueryRequest(question="Analyze the figure on page 3", workspace_id="ws-1"),
        snapshot=CorpusSnapshot(workspace_id="ws-1", eligible_doc_ids=["doc-1"]),
        interpreted_query=_interpreted_query(
            request_type=QueryRequestType.UNSUPPORTED,
            answer_shape="capability_boundary_response",
            unsupported_capability_flags=[UnsupportedCapability.IMAGE_OR_FIGURE_REASONING],
        ),
        evidence_sets=[_evidence_set()],
        context_manifest=_manifest(),
        policy=QueryPolicyDefaults.build(),
    )

    assert result.assessment.support_state is SupportState.INSUFFICIENT
    assert result.assessment.qualifying_reason_codes == [
        SupportQualifierReason.UNSUPPORTED_QUESTION_TYPE
    ]
    assert [label.value for label in result.assessment.trust_failure_labels] == ["S1"]


def test_conflict_caps_support_and_requires_qualified_uncertainty() -> None:
    policy = QueryPolicyDefaults.build()
    assessor = HybridSupportAssessor()
    evidence_set = _evidence_set(conflict_flags=["Sources disagree on the recommendation."])
    assessment = assessor.assess(
        request=QueryRequest(question="What should we do?", workspace_id="ws-1"),
        snapshot=CorpusSnapshot(workspace_id="ws-1", eligible_doc_ids=["doc-1"]),
        interpreted_query=_interpreted_query(),
        evidence_sets=[evidence_set],
        context_manifest=_manifest(),
        policy=policy,
    ).assessment

    decision = (
        DeterministicAnswerModePolicy()
        .decide(
            request=QueryRequest(question="What should we do?", workspace_id="ws-1"),
            snapshot=CorpusSnapshot(workspace_id="ws-1", eligible_doc_ids=["doc-1"]),
            interpreted_query=_interpreted_query(),
            support_assessment=assessment,
            policy=policy,
        )
        .decision
    )

    assert assessment.support_state is SupportState.PARTIAL
    assert SupportQualifierReason.MATERIAL_CONFLICT in assessment.qualifying_reason_codes
    assert decision.answer_mode is AnswerMode.QUALIFIED_UNCERTAINTY
    assert decision.must_surface_conflict is True


def test_cross_document_request_with_one_document_stays_partial() -> None:
    policy = QueryPolicyDefaults.build()
    assessment = (
        HybridSupportAssessor()
        .assess(
            request=QueryRequest(
                question="What do these documents say about embeddings?",
                workspace_id="ws-1",
            ),
            snapshot=CorpusSnapshot(workspace_id="ws-1", eligible_doc_ids=["doc-1"]),
            interpreted_query=_interpreted_query(
                request_type=QueryRequestType.SYNTHESIS,
                answer_shape="multi_source_synthesis",
                requires_synthesis=True,
                synthesis_mode=SynthesisMode.CROSS_DOCUMENT,
                specificity=QuerySpecificity.BROAD,
            ),
            evidence_sets=[_evidence_set()],
            context_manifest=_manifest(),
            policy=policy,
        )
        .assessment
    )

    decision = (
        DeterministicAnswerModePolicy()
        .decide(
            request=QueryRequest(
                question="What do these documents say about embeddings?",
                workspace_id="ws-1",
            ),
            snapshot=CorpusSnapshot(workspace_id="ws-1", eligible_doc_ids=["doc-1"]),
            interpreted_query=_interpreted_query(
                request_type=QueryRequestType.SYNTHESIS,
                answer_shape="multi_source_synthesis",
                requires_synthesis=True,
                synthesis_mode=SynthesisMode.CROSS_DOCUMENT,
                specificity=QuerySpecificity.BROAD,
            ),
            support_assessment=assessment,
            policy=policy,
        )
        .decision
    )

    assert assessment.support_state is SupportState.PARTIAL
    assert SupportQualifierReason.MISSING_MATERIAL_COVERAGE in assessment.qualifying_reason_codes
    assert decision.answer_mode is AnswerMode.QUALIFIED_ANSWER
