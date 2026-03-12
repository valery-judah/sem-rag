from __future__ import annotations

from doc_forge._contracts import SourceReference
from doc_forge.query import EvidenceGroupingMode, EvidenceSet, EvidenceUnit, QueryPolicyDefaults
from doc_forge.query.context_assembly import DeterministicContextAssembler
from doc_forge.query.contracts import (
    CorpusSnapshot,
    InterpretedQuery,
    QueryRequest,
    QueryRequestType,
    QuerySpecificity,
    RetrievedCandidate,
    SynthesisMode,
)


def _candidate(*, chunk_id: str, locator: str, retrieval_rank: int) -> RetrievedCandidate:
    return RetrievedCandidate(
        doc_id="doc-1",
        chunk_id=chunk_id,
        section_id="section-1",
        heading_path=["Chapter 1", "Retrieval"],
        locator=locator,
        retrieval_score=1.0 / retrieval_rank,
        retrieval_rank=retrieval_rank,
    )


def _unit(
    *,
    evidence_unit_id: str,
    chunk_id: str,
    locator: str,
    snippet: str,
    unit_rank: int,
) -> EvidenceUnit:
    candidate = _candidate(
        chunk_id=chunk_id,
        locator=locator,
        retrieval_rank=unit_rank,
    )
    return EvidenceUnit(
        evidence_unit_id=evidence_unit_id,
        candidate=candidate,
        source_reference=SourceReference(
            doc_id="doc-1",
            document_title="Doc 1",
            snippet=snippet,
            section_id="section-1",
            heading_path=["Chapter 1", "Retrieval"],
            page_label=locator,
            chunk_id=chunk_id,
            passage_anchor=locator,
        ),
        unit_rank=unit_rank,
        selection_reason="selected for testing",
    )


def _evidence_set(*, evidence_set_id: str, snippet: str, locator: str) -> EvidenceSet:
    return EvidenceSet(
        evidence_set_id=evidence_set_id,
        grouping_mode=EvidenceGroupingMode.SINGLE_PASSAGE,
        evidence_units=[
            _unit(
                evidence_unit_id=f"eu-{evidence_set_id}",
                chunk_id=f"chunk-{evidence_set_id}",
                locator=locator,
                snippet=snippet,
                unit_rank=1,
            )
        ],
        purpose="direct_support",
        coverage_notes=[],
        conflict_flags=[],
        assembly_reason="assembled for testing",
    )


def _interpreted_query() -> InterpretedQuery:
    return InterpretedQuery(
        normalized_question="what is semantic retrieval",
        request_type=QueryRequestType.FACT_LOOKUP,
        answer_shape="short answer",
        specificity=QuerySpecificity.PRECISE,
        scope_hints=["retrieval"],
        requires_synthesis=False,
        synthesis_mode=SynthesisMode.NONE,
        requires_source_navigation=False,
        unsupported_capability_flags=[],
        normalization_notes=[],
    )


def _snapshot() -> CorpusSnapshot:
    return CorpusSnapshot(
        workspace_id="ws-1",
        eligible_doc_ids=["doc-1"],
    )


def test_context_assembly_drops_lower_priority_evidence_sets_when_over_budget() -> None:
    assembler = DeterministicContextAssembler()
    policy = QueryPolicyDefaults.build().model_copy(update={"context_token_budget": 50})
    result = assembler.assemble(
        request=QueryRequest(question="What is semantic retrieval?", workspace_id="ws-1"),
        snapshot=_snapshot(),
        interpreted_query=_interpreted_query(),
        evidence_sets=[
            _evidence_set(
                evidence_set_id="es-1",
                locator="p. 1",
                snippet="Short primary support.",
            ),
            _evidence_set(
                evidence_set_id="es-2",
                locator="p. 2",
                snippet=(
                    "This support block is intentionally much longer so it consumes "
                    "more of the deterministic token budget."
                ),
            ),
            _evidence_set(
                evidence_set_id="es-3",
                locator="p. 3",
                snippet="Short secondary support.",
            ),
        ],
        policy=policy,
    )

    assert result.manifest.ordered_evidence_set_ids == ["es-1", "es-2", "es-3"]
    assert result.manifest.included_evidence_set_ids == ["es-1", "es-3"]
    assert result.manifest.dropped_evidence_set_ids == ["es-2"]
    assert result.manifest.exclusion_reasons == {"es-2": "dropped_over_budget"}


def test_context_assembly_drops_duplicate_renderings_and_records_notes() -> None:
    assembler = DeterministicContextAssembler()
    result = assembler.assemble(
        request=QueryRequest(question="What is semantic retrieval?", workspace_id="ws-1"),
        snapshot=_snapshot(),
        interpreted_query=_interpreted_query(),
        evidence_sets=[
            _evidence_set(
                evidence_set_id="es-1",
                locator="p. 1",
                snippet="Repeated support block.",
            ),
            _evidence_set(
                evidence_set_id="es-2",
                locator="p. 1",
                snippet="Repeated support block.",
            ),
        ],
        policy=QueryPolicyDefaults.build(),
    )

    assert result.manifest.included_evidence_set_ids == ["es-1"]
    assert result.manifest.dropped_evidence_set_ids == ["es-2"]
    assert result.manifest.exclusion_reasons["es-2"] == "dropped_duplicate_rendering"
    assert any(
        "es-2 dropped because rendered context duplicated an earlier item" in note
        for note in result.manifest.duplicate_suppression_notes
    )


def test_context_assembly_context_items_match_included_evidence_set_ids() -> None:
    assembler = DeterministicContextAssembler()
    result = assembler.assemble(
        request=QueryRequest(question="What is semantic retrieval?", workspace_id="ws-1"),
        snapshot=_snapshot(),
        interpreted_query=_interpreted_query(),
        evidence_sets=[
            _evidence_set(
                evidence_set_id="es-1",
                locator="p. 1",
                snippet="Primary support block.",
            ),
        ],
        policy=QueryPolicyDefaults.build(),
    )

    assert [item.evidence_set_id for item in result.manifest.context_items] == ["es-1"]
    assert result.manifest.included_evidence_set_ids == ["es-1"]


def test_context_assembly_prefixes_multi_document_snippets_with_document_titles() -> None:
    assembler = DeterministicContextAssembler()
    result = assembler.assemble(
        request=QueryRequest(
            question="Compare Atlas and Beacon caching strategies.",
            workspace_id="ws-1",
        ),
        snapshot=_snapshot(),
        interpreted_query=InterpretedQuery(
            normalized_question="compare atlas and beacon caching strategies",
            request_type=QueryRequestType.COMPARISON,
            answer_shape="qualified_comparison",
            specificity=QuerySpecificity.BROAD,
            scope_hints=["atlas", "beacon", "caching"],
            requires_synthesis=True,
            synthesis_mode=SynthesisMode.CROSS_DOCUMENT,
            requires_source_navigation=False,
            unsupported_capability_flags=[],
            normalization_notes=[],
        ),
        evidence_sets=[
            EvidenceSet(
                evidence_set_id="es-1",
                grouping_mode=EvidenceGroupingMode.MULTI_DOCUMENT,
                evidence_units=[
                    EvidenceUnit(
                        evidence_unit_id="eu-atlas",
                        candidate=RetrievedCandidate(
                            doc_id="doc-atlas",
                            chunk_id="chunk-atlas",
                            section_id="section-atlas",
                            heading_path=["Atlas", "Caching"],
                            locator="p. 2",
                            retrieval_score=0.9,
                            retrieval_rank=1,
                        ),
                        source_reference=SourceReference(
                            doc_id="doc-atlas",
                            document_title="Atlas Cache Design",
                            snippet="Atlas uses immediate invalidation.",
                            section_id="section-atlas",
                            heading_path=["Atlas", "Caching"],
                            page_label="p. 2",
                            chunk_id="chunk-atlas",
                            passage_anchor="doc-atlas#chunk-atlas",
                        ),
                        unit_rank=1,
                        selection_reason="selected for comparison",
                    ),
                    EvidenceUnit(
                        evidence_unit_id="eu-beacon",
                        candidate=RetrievedCandidate(
                            doc_id="doc-beacon",
                            chunk_id="chunk-beacon",
                            section_id="section-beacon",
                            heading_path=["Beacon", "Caching"],
                            locator="p. 4",
                            retrieval_score=0.89,
                            retrieval_rank=2,
                        ),
                        source_reference=SourceReference(
                            doc_id="doc-beacon",
                            document_title="Beacon Dashboard Cache",
                            snippet="Beacon uses a 15-minute TTL and allows stale reads.",
                            section_id="section-beacon",
                            heading_path=["Beacon", "Caching"],
                            page_label="p. 4",
                            chunk_id="chunk-beacon",
                            passage_anchor="doc-beacon#chunk-beacon",
                        ),
                        unit_rank=2,
                        selection_reason="selected for comparison",
                    ),
                ],
                purpose="cross_document_synthesis",
                coverage_notes=[],
                conflict_flags=[],
                assembly_reason="assembled for comparison test",
            )
        ],
        policy=QueryPolicyDefaults.build(),
    )

    rendered = result.manifest.context_items[0].rendered_text
    assert "Atlas Cache Design: Atlas uses immediate invalidation." in rendered
    assert "Beacon Dashboard Cache: Beacon uses a 15-minute TTL and allows stale reads." in rendered
