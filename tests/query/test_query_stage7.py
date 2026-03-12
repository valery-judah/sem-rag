from __future__ import annotations

import pytest

from doc_forge._contracts import SourceReference
from doc_forge.query.answer_generation import DeterministicGroundedAnswerGenerator
from doc_forge.query.citation_rendering import DeterministicCitationRenderer
from doc_forge.query.contracts import (
    AnswerDraft,
    AnswerMode,
    AnswerModeDecision,
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
    SupportAssessment,
    SupportQualifierReason,
    SupportState,
    SynthesisMode,
)
from doc_forge.query.errors import QueryStageContractViolationError
from doc_forge.query.policies import QueryPolicyDefaults


def _candidate(
    *,
    doc_id: str = "doc-1",
    chunk_id: str = "chunk-1",
    locator: str = "p. 2",
) -> RetrievedCandidate:
    return RetrievedCandidate(
        doc_id=doc_id,
        chunk_id=chunk_id,
        section_id="section-1",
        heading_path=["Chapter 1", "Overview"],
        locator=locator,
        retrieval_score=0.9,
        retrieval_rank=1,
    )


def _source_reference(
    *,
    doc_id: str = "doc-1",
    title: str = "Doc 1",
    snippet: str = "Vector search uses embeddings to retrieve related passages.",
    page_label: str | None = "p. 2",
    passage_anchor: str | None = "doc-1#chunk-1",
) -> SourceReference:
    return SourceReference(
        doc_id=doc_id,
        document_title=title,
        snippet=snippet,
        section_id="section-1",
        heading_path=["Chapter 1", "Overview"],
        page_label=page_label,
        chunk_id=f"{doc_id}-chunk-1",
        passage_anchor=passage_anchor,
    )


def _evidence_set(
    *,
    evidence_set_id: str = "es-1",
    doc_id: str = "doc-1",
    title: str = "Doc 1",
    snippet: str = "Vector search uses embeddings to retrieve related passages.",
    page_label: str | None = "p. 2",
) -> EvidenceSet:
    return EvidenceSet(
        evidence_set_id=evidence_set_id,
        grouping_mode=EvidenceGroupingMode.SINGLE_PASSAGE,
        evidence_units=[
            EvidenceUnit(
                evidence_unit_id=f"{evidence_set_id}-u1",
                candidate=_candidate(
                    doc_id=doc_id,
                    chunk_id=f"{doc_id}-chunk-1",
                    locator=page_label or "anchor",
                ),
                source_reference=_source_reference(
                    doc_id=doc_id,
                    title=title,
                    snippet=snippet,
                    page_label=page_label,
                    passage_anchor=f"{doc_id}#chunk-1",
                ),
                unit_rank=1,
                selection_reason="direct support",
            )
        ],
        purpose="direct_support",
        coverage_notes=[],
        conflict_flags=[],
        assembly_reason="built for test",
    )


def _context_manifest(*, evidence_set_ids: list[str]) -> ContextManifest:
    return ContextManifest(
        ordered_evidence_set_ids=list(evidence_set_ids),
        included_evidence_set_ids=list(evidence_set_ids),
        inclusion_reasons={
            evidence_set_id: "included_within_budget" for evidence_set_id in evidence_set_ids
        },
        token_budget=4000,
        token_budget_used=32,
        context_items=[
            ContextItem(
                evidence_set_id=evidence_set_id,
                assembly_rank=index + 1,
                rendered_text=(
                    f"Doc {index + 1} | direct_support | Chapter 1 > Overview\n"
                    f"[p. {index + 2}] Vector search uses embeddings to retrieve related passages."
                ),
                contributing_doc_ids=[f"doc-{index + 1}"],
                heading_paths=[["Chapter 1", "Overview"]],
                locators=[f"p. {index + 2}"],
                estimated_token_count=16,
            )
            for index, evidence_set_id in enumerate(evidence_set_ids)
        ],
    )


def _interpreted_query(
    *, requires_synthesis: bool = False, **overrides: object
) -> InterpretedQuery:
    return InterpretedQuery(
        normalized_question="what uses embeddings to retrieve related passages",
        request_type=QueryRequestType.FACT_LOOKUP,
        answer_shape="direct answer",
        specificity=QuerySpecificity.PRECISE,
        requires_synthesis=requires_synthesis,
        synthesis_mode=SynthesisMode.CROSS_DOCUMENT if requires_synthesis else SynthesisMode.NONE,
        requires_source_navigation=False,
        unsupported_capability_flags=[],
        normalization_notes=[],
    ).model_copy(update=overrides)


def test_grounded_generator_returns_direct_answer_with_grounded_ids() -> None:
    generator = DeterministicGroundedAnswerGenerator()

    result = generator.generate(
        request=QueryRequest(
            question="What uses embeddings to retrieve related passages?",
            workspace_id="ws-1",
        ),
        snapshot=CorpusSnapshot(workspace_id="ws-1", eligible_doc_ids=["doc-1"]),
        interpreted_query=_interpreted_query(),
        context_manifest=_context_manifest(evidence_set_ids=["es-1"]),
        support_assessment=SupportAssessment(support_state=SupportState.SUFFICIENT),
        answer_mode_decision=AnswerModeDecision(
            answer_mode=AnswerMode.DIRECT_ANSWER,
            rationale="Sufficient support allows a direct answer.",
            based_on_support_state=SupportState.SUFFICIENT,
        ),
        policy=QueryPolicyDefaults.build(),
    )

    assert (
        "Vector search uses embeddings to retrieve related passages."
        in result.answer_draft.answer_text
    )
    assert result.answer_draft.grounded_evidence_set_ids == ["es-1"]
    assert result.answer_draft.should_render_citations is True


def test_grounded_generator_returns_honest_full_abstention_without_citations() -> None:
    generator = DeterministicGroundedAnswerGenerator()

    result = generator.generate(
        request=QueryRequest(question="What is available in the corpus?", workspace_id="ws-1"),
        snapshot=CorpusSnapshot(workspace_id="ws-1", eligible_doc_ids=[]),
        interpreted_query=_interpreted_query(),
        context_manifest=_context_manifest(evidence_set_ids=[]),
        support_assessment=SupportAssessment(
            support_state=SupportState.INSUFFICIENT,
            qualifying_reason_codes=[SupportQualifierReason.NO_EVIDENCE_AVAILABLE],
        ),
        answer_mode_decision=AnswerModeDecision(
            answer_mode=AnswerMode.FULL_ABSTENTION,
            rationale="Insufficient support requires abstention.",
            based_on_support_state=SupportState.INSUFFICIENT,
        ),
        policy=QueryPolicyDefaults.build(),
    )

    assert "does not provide enough support" in result.answer_draft.answer_text
    assert result.answer_draft.grounded_evidence_set_ids == []
    assert result.answer_draft.should_render_citations is False


def test_citation_renderer_requires_grounded_evidence_ids_for_cited_answers() -> None:
    renderer = DeterministicCitationRenderer()

    with pytest.raises(
        QueryStageContractViolationError,
        match="grounded evidence set ids",
    ):
        renderer.render(
            interpreted_query=_interpreted_query(),
            evidence_sets=[_evidence_set()],
            context_manifest=_context_manifest(evidence_set_ids=["es-1"]),
            support_assessment=SupportAssessment(support_state=SupportState.SUFFICIENT),
            answer_mode_decision=AnswerModeDecision(
                answer_mode=AnswerMode.DIRECT_ANSWER,
                rationale="Sufficient support allows a direct answer.",
                based_on_support_state=SupportState.SUFFICIENT,
            ),
            answer_draft=AnswerDraft(
                answer_text="Vector search uses embeddings to retrieve related passages.",
                grounded_evidence_set_ids=[],
                generator_version="answer_generation.deterministic.v1",
            ),
            policy=QueryPolicyDefaults.build(),
        )


def test_citation_renderer_returns_multi_document_citations_for_synthesis() -> None:
    renderer = DeterministicCitationRenderer()
    evidence_sets = [
        _evidence_set(evidence_set_id="es-1", doc_id="doc-1", title="Doc 1"),
        _evidence_set(evidence_set_id="es-2", doc_id="doc-2", title="Doc 2", page_label="p. 5"),
    ]

    result = renderer.render(
        interpreted_query=_interpreted_query(requires_synthesis=True),
        evidence_sets=evidence_sets,
        context_manifest=_context_manifest(evidence_set_ids=["es-1", "es-2"]),
        support_assessment=SupportAssessment(support_state=SupportState.SUFFICIENT),
        answer_mode_decision=AnswerModeDecision(
            answer_mode=AnswerMode.DIRECT_ANSWER,
            rationale="Sufficient support allows a direct answer.",
            based_on_support_state=SupportState.SUFFICIENT,
        ),
        answer_draft=AnswerDraft(
            answer_text="The corpus supports the answer across multiple documents.",
            grounded_evidence_set_ids=["es-1", "es-2"],
            generator_version="answer_generation.deterministic.v1",
        ),
        policy=QueryPolicyDefaults.build(),
    )

    assert len(result.citation_bundle.citations) == 2
    assert result.citation_bundle.material_doc_ids == ["doc-1", "doc-2"]


def test_grounded_generator_returns_comparison_answer_that_mentions_both_documents() -> None:
    generator = DeterministicGroundedAnswerGenerator()

    result = generator.generate(
        request=QueryRequest(
            question="Compare Atlas and Beacon caching strategies. Which is stricter?",
            workspace_id="ws-1",
        ),
        snapshot=CorpusSnapshot(workspace_id="ws-1", eligible_doc_ids=["doc-atlas", "doc-beacon"]),
        interpreted_query=_interpreted_query(
            requires_synthesis=True,
            normalized_question="compare atlas and beacon caching strategies which is stricter",
            request_type=QueryRequestType.COMPARISON,
            answer_shape="qualified_comparison",
            specificity=QuerySpecificity.BROAD,
        ),
        context_manifest=ContextManifest(
            ordered_evidence_set_ids=["es-1"],
            included_evidence_set_ids=["es-1"],
            inclusion_reasons={"es-1": "included_within_budget"},
            token_budget=4000,
            token_budget_used=64,
            context_items=[
                ContextItem(
                    evidence_set_id="es-1",
                    assembly_rank=1,
                    rendered_text=(
                        "Atlas Cache Design | cross_document_synthesis | Atlas > Caching\n"
                        "[p. 2] Atlas Cache Design: Atlas uses a write-through cache "
                        "and immediate invalidation.\n"
                        "[p. 4] Beacon Dashboard Cache: Beacon uses a 15-minute TTL "
                        "and allows stale reads."
                    ),
                    contributing_doc_ids=["doc-atlas", "doc-beacon"],
                    heading_paths=[["Atlas", "Caching"], ["Beacon", "Caching"]],
                    locators=["p. 2", "p. 4"],
                    estimated_token_count=32,
                )
            ],
        ),
        support_assessment=SupportAssessment(support_state=SupportState.SUFFICIENT),
        answer_mode_decision=AnswerModeDecision(
            answer_mode=AnswerMode.DIRECT_ANSWER,
            rationale="Sufficient support allows a direct answer.",
            based_on_support_state=SupportState.SUFFICIENT,
        ),
        policy=QueryPolicyDefaults.build(),
    )

    assert "Atlas Cache Design has stricter freshness guarantees" in result.answer_draft.answer_text
    assert "Beacon Dashboard Cache is looser" in result.answer_draft.answer_text
