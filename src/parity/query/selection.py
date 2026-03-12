"""Deterministic Stage-4 selection and evidence-set construction helpers."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from parity._contracts import SourceReference
from parity.readmodels import (
    QueryableChunkRecord,
    QueryableCorpusReadModel,
    QueryableDocumentRecord,
)

from .contracts import (
    CorpusSnapshot,
    DuplicateSuppressionMode,
    EvidenceGroupingMode,
    EvidenceSet,
    EvidenceUnit,
    InterpretedQuery,
    QueryRequest,
    QueryRequestType,
    QuerySpecificity,
    RetrievedCandidate,
    SynthesisMode,
)
from .policies import QueryPolicy


@dataclass(frozen=True)
class SnapshotSelectionIndex:
    """In-memory snapshot-local lookup surfaces for Stage 4."""

    documents_by_id: dict[str, QueryableDocumentRecord]
    chunks_by_id: dict[str, QueryableChunkRecord]
    chunks_by_doc_and_ordinal: dict[str, dict[int, QueryableChunkRecord]]


class SelectionDecision(BaseModel):
    """Structured keep/drop decision for one retrieved candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate: RetrievedCandidate
    status: str = Field(min_length=1)
    final_rank: int | None = Field(default=None, ge=1)
    rerank_score: float
    rerank_signals: dict[str, float] = Field(default_factory=dict)
    drop_reason: str | None = None
    duplicate_of_chunk_id: str | None = None


class NeighborExpansionRecord(BaseModel):
    """Structured note for one neighbor expansion action."""

    model_config = ConfigDict(extra="forbid")

    anchor_chunk_id: str = Field(min_length=1)
    added_chunk_ids: list[str] = Field(default_factory=list)
    skipped_chunk_ids: list[str] = Field(default_factory=list)


class SelectionResult(BaseModel):
    """Structured Stage-4 output consumed by the select stage."""

    model_config = ConfigDict(extra="forbid")

    selected_candidates: list[RetrievedCandidate] = Field(default_factory=list)
    evidence_sets: list[EvidenceSet] = Field(default_factory=list)
    decisions: list[SelectionDecision] = Field(default_factory=list)
    duplicate_suppression_notes: list[str] = Field(default_factory=list)
    neighbor_expansion_notes: list[NeighborExpansionRecord] = Field(default_factory=list)


class QuerySelector(Protocol):
    """Selection-stage seam for deterministic candidate structuring."""

    def select(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        retrieved_candidates: list[RetrievedCandidate],
        policy: QueryPolicy,
    ) -> SelectionResult:
        """Return selected candidates and explicit evidence sets."""
        ...


class DeterministicQuerySelector:
    """Deterministic Stage-4 selector over snapshot-scoped candidates."""

    def __init__(self, *, corpus_read_model: QueryableCorpusReadModel) -> None:
        self._corpus_read_model = corpus_read_model

    def select(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        retrieved_candidates: list[RetrievedCandidate],
        policy: QueryPolicy,
    ) -> SelectionResult:
        del request
        index = self._build_index(snapshot)
        ranked = self._rerank_candidates(
            retrieved_candidates=retrieved_candidates,
            interpreted_query=interpreted_query,
            index=index,
        )
        survivors, dropped_duplicates, duplicate_notes = self._suppress_duplicates(
            ranked,
            policy.duplicate_suppression_mode,
        )
        evidence_sets, neighbor_notes = self._build_evidence_sets(
            survivors=survivors,
            interpreted_query=interpreted_query,
            index=index,
            policy=policy,
        )
        selected_candidates = _flatten_selected_candidates(evidence_sets)
        selected_chunk_ids = {candidate.chunk_id for candidate in selected_candidates}
        decisions = _finalize_decisions(
            ranked=ranked,
            dropped_duplicates=dropped_duplicates,
            selected_chunk_ids=selected_chunk_ids,
        )
        return SelectionResult(
            selected_candidates=selected_candidates,
            evidence_sets=evidence_sets,
            decisions=decisions,
            duplicate_suppression_notes=duplicate_notes,
            neighbor_expansion_notes=neighbor_notes,
        )

    def _build_index(self, snapshot: CorpusSnapshot) -> SnapshotSelectionIndex:
        eligible_doc_ids = set(snapshot.eligible_doc_ids)
        documents_by_id = {
            document.doc_id: document
            for document in self._corpus_read_model.list_ready_documents(snapshot.workspace_id)
            if document.doc_id in eligible_doc_ids
        }
        chunks = self._corpus_read_model.list_chunks_for_snapshot(snapshot)
        chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
        chunks_by_doc_and_ordinal: dict[str, dict[int, QueryableChunkRecord]] = defaultdict(dict)
        for chunk in chunks:
            chunks_by_doc_and_ordinal[chunk.doc_id][chunk.ordinal] = chunk
        return SnapshotSelectionIndex(
            documents_by_id=documents_by_id,
            chunks_by_id=chunks_by_id,
            chunks_by_doc_and_ordinal=dict(chunks_by_doc_and_ordinal),
        )

    def _rerank_candidates(
        self,
        *,
        retrieved_candidates: list[RetrievedCandidate],
        interpreted_query: InterpretedQuery,
        index: SnapshotSelectionIndex,
    ) -> list[SelectionDecision]:
        decisions: list[SelectionDecision] = []
        for candidate in retrieved_candidates:
            rerank_signals = _compute_rerank_signals(
                candidate=candidate,
                interpreted_query=interpreted_query,
                chunk=index.chunks_by_id.get(candidate.chunk_id),
                document=index.documents_by_id.get(candidate.doc_id),
            )
            decisions.append(
                SelectionDecision(
                    candidate=candidate,
                    status="ranked",
                    rerank_score=sum(rerank_signals.values()),
                    rerank_signals=rerank_signals,
                )
            )
        return sorted(
            decisions,
            key=lambda decision: (
                -decision.rerank_score,
                decision.candidate.retrieval_rank,
                decision.candidate.doc_id,
                decision.candidate.chunk_id,
            ),
        )

    def _suppress_duplicates(
        self,
        decisions: list[SelectionDecision],
        mode: DuplicateSuppressionMode,
    ) -> tuple[list[SelectionDecision], dict[str, SelectionDecision], list[str]]:
        seen: dict[tuple[object, ...], SelectionDecision] = {}
        survivors: list[SelectionDecision] = []
        dropped: dict[str, SelectionDecision] = {}
        notes: list[str] = []
        for decision in decisions:
            key = _duplicate_key(decision.candidate, mode)
            existing = seen.get(key)
            if existing is None:
                seen[key] = decision
                survivors.append(decision)
                continue
            duplicate = decision.model_copy(
                update={
                    "status": "dropped",
                    "drop_reason": "duplicate_suppression",
                    "duplicate_of_chunk_id": existing.candidate.chunk_id,
                }
            )
            dropped[decision.candidate.chunk_id] = duplicate
            notes.append(
                f"{decision.candidate.chunk_id} suppressed as duplicate of "
                f"{existing.candidate.chunk_id}"
            )
        return survivors, dropped, notes

    def _build_evidence_sets(
        self,
        *,
        survivors: list[SelectionDecision],
        interpreted_query: InterpretedQuery,
        index: SnapshotSelectionIndex,
        policy: QueryPolicy,
    ) -> tuple[list[EvidenceSet], list[NeighborExpansionRecord]]:
        if not survivors:
            return [], []
        if interpreted_query.requires_synthesis or (
            interpreted_query.synthesis_mode is SynthesisMode.CROSS_DOCUMENT
        ):
            return self._build_multi_document_sets(
                survivors=survivors,
                interpreted_query=interpreted_query,
                index=index,
                policy=policy,
            )
        if interpreted_query.request_type is QueryRequestType.EXPLANATION or (
            interpreted_query.specificity is QuerySpecificity.SECTION_SCOPED
        ):
            return self._build_same_document_sets(
                survivors=survivors,
                interpreted_query=interpreted_query,
                index=index,
                policy=policy,
            )
        return self._build_atomic_sets(
            survivors=survivors,
            interpreted_query=interpreted_query,
            index=index,
            policy=policy,
        )

    def _build_multi_document_sets(
        self,
        *,
        survivors: list[SelectionDecision],
        interpreted_query: InterpretedQuery,
        index: SnapshotSelectionIndex,
        policy: QueryPolicy,
    ) -> tuple[list[EvidenceSet], list[NeighborExpansionRecord]]:
        units: list[EvidenceUnit] = []
        selected_docs: set[str] = set()
        selected_doc_cap = (
            2
            if interpreted_query.request_type is QueryRequestType.COMPARISON
            else min(3, policy.evidence_set_cap)
        )
        comparison_targeted = [
            decision
            for decision in survivors
            if decision.rerank_signals.get("comparison_target_bonus", 0.0) > 0.0
        ]
        source_decisions = survivors
        if (
            interpreted_query.request_type is QueryRequestType.COMPARISON
            and len({decision.candidate.doc_id for decision in comparison_targeted}) >= 2
        ):
            source_decisions = comparison_targeted

        for decision in source_decisions:
            candidate = decision.candidate
            if candidate.doc_id in selected_docs:
                continue
            units.append(
                _make_evidence_unit(
                    candidate=candidate,
                    chunk=index.chunks_by_id[candidate.chunk_id],
                    document=index.documents_by_id[candidate.doc_id],
                    unit_rank=len(units) + 1,
                    added_by_neighbor_expansion=False,
                    selection_reason="selected for cross-document synthesis coverage",
                )
            )
            selected_docs.add(candidate.doc_id)
            if len(units) >= selected_doc_cap:
                break
        if not units:
            return [], []
        grouping_mode = (
            EvidenceGroupingMode.MULTI_DOCUMENT
            if len({unit.candidate.doc_id for unit in units}) > 1
            else EvidenceGroupingMode.SINGLE_PASSAGE
        )
        evidence_set = _build_evidence_set(
            evidence_set_id="es-1",
            grouping_mode=grouping_mode,
            evidence_units=units,
            purpose="cross_document_synthesis",
            coverage_notes=["Preserves one high-value support unit per contributing document."],
            conflict_flags=[],
            assembly_reason=(
                "Built from top distinct documents because interpretation requires synthesis."
            ),
        )
        return [evidence_set], []

    def _build_same_document_sets(
        self,
        *,
        survivors: list[SelectionDecision],
        interpreted_query: InterpretedQuery,
        index: SnapshotSelectionIndex,
        policy: QueryPolicy,
    ) -> tuple[list[EvidenceSet], list[NeighborExpansionRecord]]:
        evidence_sets: list[EvidenceSet] = []
        neighbor_notes: list[NeighborExpansionRecord] = []
        used_chunk_ids: set[str] = set()
        for decision in survivors:
            candidate = decision.candidate
            if candidate.chunk_id in used_chunk_ids:
                continue
            chunk = index.chunks_by_id[candidate.chunk_id]
            primary_units = [
                _make_evidence_unit(
                    candidate=candidate,
                    chunk=chunk,
                    document=index.documents_by_id[candidate.doc_id],
                    unit_rank=1,
                    added_by_neighbor_expansion=False,
                    selection_reason="highest-value same-document support unit",
                )
            ]
            related_units: list[EvidenceUnit] = []
            for other in survivors:
                other_candidate = other.candidate
                if (
                    other_candidate.chunk_id == candidate.chunk_id
                    or other_candidate.chunk_id in used_chunk_ids
                ):
                    continue
                if other_candidate.doc_id != candidate.doc_id:
                    continue
                other_chunk = index.chunks_by_id[other_candidate.chunk_id]
                if not _is_same_document_group_candidate(chunk, other_chunk):
                    continue
                related_units.append(
                    _make_evidence_unit(
                        candidate=other_candidate,
                        chunk=other_chunk,
                        document=index.documents_by_id[other_candidate.doc_id],
                        unit_rank=len(primary_units) + len(related_units) + 1,
                        added_by_neighbor_expansion=False,
                        selection_reason="selected to improve same-document coverage",
                    )
                )
                if len(primary_units) + len(related_units) >= 3:
                    break
            expanded_units, note = _expand_neighbors(
                primary_candidate=candidate,
                index=index,
                policy=policy,
                existing_chunk_ids={
                    unit.candidate.chunk_id for unit in primary_units + related_units
                },
                start_rank=len(primary_units) + len(related_units) + 1,
            )
            if note is not None:
                neighbor_notes.append(note)
            units = primary_units + related_units + expanded_units
            for unit in units:
                used_chunk_ids.add(unit.candidate.chunk_id)
            grouping_mode = _grouping_mode_for_units(
                interpreted_query=interpreted_query,
                units=units,
            )
            evidence_sets.append(
                _build_evidence_set(
                    evidence_set_id=f"es-{len(evidence_sets) + 1}",
                    grouping_mode=grouping_mode,
                    evidence_units=units,
                    purpose="same_document_explanation",
                    coverage_notes=[
                        "Groups nearby or same-section passages to preserve explanatory continuity."
                    ],
                    conflict_flags=[],
                    assembly_reason=(
                        "Built from same-document evidence because the question "
                        "requests explanation or section-scoped coverage."
                    ),
                )
            )
            if len(evidence_sets) >= policy.evidence_set_cap:
                break
        return evidence_sets, neighbor_notes

    def _build_atomic_sets(
        self,
        *,
        survivors: list[SelectionDecision],
        interpreted_query: InterpretedQuery,
        index: SnapshotSelectionIndex,
        policy: QueryPolicy,
    ) -> tuple[list[EvidenceSet], list[NeighborExpansionRecord]]:
        evidence_sets: list[EvidenceSet] = []
        neighbor_notes: list[NeighborExpansionRecord] = []
        for decision in survivors[: policy.evidence_set_cap]:
            candidate = decision.candidate
            chunk = index.chunks_by_id[candidate.chunk_id]
            units = [
                _make_evidence_unit(
                    candidate=candidate,
                    chunk=chunk,
                    document=index.documents_by_id[candidate.doc_id],
                    unit_rank=1,
                    added_by_neighbor_expansion=False,
                    selection_reason="direct support candidate selected after reranking",
                )
            ]
            expanded_units, note = _expand_neighbors(
                primary_candidate=candidate,
                index=index,
                policy=policy,
                existing_chunk_ids={candidate.chunk_id},
                start_rank=2,
            )
            units.extend(expanded_units)
            if note is not None:
                neighbor_notes.append(note)
            grouping_mode = _grouping_mode_for_units(
                interpreted_query=interpreted_query,
                units=units,
            )
            evidence_sets.append(
                _build_evidence_set(
                    evidence_set_id=f"es-{len(evidence_sets) + 1}",
                    grouping_mode=grouping_mode,
                    evidence_units=units,
                    purpose=(
                        "source_navigation"
                        if interpreted_query.requires_source_navigation
                        else "direct_support"
                    ),
                    coverage_notes=[
                        "Preserves one primary support passage and optional adjacent coherence."
                    ],
                    conflict_flags=[],
                    assembly_reason=(
                        "Built as an atomic evidence set because the question does not require "
                        "broad same-document or cross-document grouping."
                    ),
                )
            )
        return evidence_sets, neighbor_notes


def _compute_rerank_signals(
    *,
    candidate: RetrievedCandidate,
    interpreted_query: InterpretedQuery,
    chunk: QueryableChunkRecord | None,
    document: QueryableDocumentRecord | None,
) -> dict[str, float]:
    heading_text = " ".join(candidate.heading_path).lower()
    chunk_text = "" if chunk is None else chunk.text.lower()
    document_title = "" if document is None else document.title.lower()
    scope_bonus = 0.0
    for hint in interpreted_query.scope_hints:
        if hint.lower() in heading_text:
            scope_bonus += 0.1
    comparison_target_bonus = 0.0
    if interpreted_query.request_type is QueryRequestType.COMPARISON:
        for hint in interpreted_query.scope_hints:
            normalized_hint = hint.lower()
            if normalized_hint in document_title:
                comparison_target_bonus += 0.35
            if normalized_hint in chunk_text:
                comparison_target_bonus += 0.2
    provenance_bonus = 0.1 if candidate.locator and candidate.heading_path else 0.0
    source_navigation_bonus = (
        0.15
        if interpreted_query.requires_source_navigation
        and (candidate.section_id is not None or candidate.locator is not None)
        else 0.0
    )
    local_coherence_bonus = 0.0
    if interpreted_query.request_type is QueryRequestType.EXPLANATION and chunk is not None:
        if chunk.section_id is not None or len(chunk.heading_path) > 1:
            local_coherence_bonus = 0.1
    specificity_bonus = (
        0.05
        if (
            interpreted_query.specificity is QuerySpecificity.PRECISE
            and candidate.section_id is not None
        )
        else 0.0
    )
    return {
        "retrieval_score": candidate.retrieval_score,
        "scope_hint_bonus": scope_bonus,
        "comparison_target_bonus": comparison_target_bonus,
        "source_navigation_bonus": source_navigation_bonus,
        "local_coherence_bonus": local_coherence_bonus,
        "provenance_bonus": provenance_bonus,
        "specificity_bonus": specificity_bonus,
    }


def _duplicate_key(
    candidate: RetrievedCandidate,
    mode: DuplicateSuppressionMode,
) -> tuple[object, ...]:
    if mode is DuplicateSuppressionMode.EXACT_SPAN:
        return (candidate.doc_id, candidate.chunk_id)
    return (
        candidate.doc_id,
        tuple(candidate.heading_path),
        candidate.locator,
        candidate.section_id,
    )


def _make_evidence_unit(
    *,
    candidate: RetrievedCandidate,
    chunk: QueryableChunkRecord,
    document: QueryableDocumentRecord,
    unit_rank: int,
    added_by_neighbor_expansion: bool,
    selection_reason: str,
) -> EvidenceUnit:
    page_label = None
    if chunk.page_start is not None:
        if chunk.page_end is None or chunk.page_end == chunk.page_start:
            page_label = f"p. {chunk.page_start}"
        else:
            page_label = f"pp. {chunk.page_start}-{chunk.page_end}"
    return EvidenceUnit(
        evidence_unit_id=f"eu-{candidate.chunk_id}",
        candidate=candidate,
        source_reference=SourceReference(
            doc_id=document.doc_id,
            document_title=document.title,
            snippet=chunk.text,
            section_id=chunk.section_id,
            heading_path=chunk.heading_path,
            page_label=page_label,
            chunk_id=chunk.chunk_id,
            passage_anchor=candidate.locator,
        ),
        unit_rank=unit_rank,
        added_by_neighbor_expansion=added_by_neighbor_expansion,
        selection_reason=selection_reason,
    )


def _build_evidence_set(
    *,
    evidence_set_id: str,
    grouping_mode: EvidenceGroupingMode,
    evidence_units: list[EvidenceUnit],
    purpose: str,
    coverage_notes: list[str],
    conflict_flags: list[str],
    assembly_reason: str,
) -> EvidenceSet:
    return EvidenceSet(
        evidence_set_id=evidence_set_id,
        grouping_mode=grouping_mode,
        evidence_units=evidence_units,
        purpose=purpose,
        coverage_notes=coverage_notes,
        conflict_flags=conflict_flags,
        assembly_reason=assembly_reason,
    )


def _expand_neighbors(
    *,
    primary_candidate: RetrievedCandidate,
    index: SnapshotSelectionIndex,
    policy: QueryPolicy,
    existing_chunk_ids: set[str],
    start_rank: int,
) -> tuple[list[EvidenceUnit], NeighborExpansionRecord | None]:
    if not policy.neighbor_expansion_enabled or policy.neighbor_expansion_cap == 0:
        return [], None
    primary_chunk = index.chunks_by_id[primary_candidate.chunk_id]
    doc_chunks = index.chunks_by_doc_and_ordinal.get(primary_candidate.doc_id, {})
    added_units: list[EvidenceUnit] = []
    added_chunk_ids: list[str] = []
    skipped_chunk_ids: list[str] = []
    for offset in (1, -1):
        if len(added_units) >= policy.neighbor_expansion_cap:
            break
        neighbor = doc_chunks.get(primary_chunk.ordinal + offset)
        if neighbor is None:
            continue
        if neighbor.chunk_id in existing_chunk_ids:
            continue
        if not _is_neighbor_expandable(primary_chunk, neighbor):
            skipped_chunk_ids.append(neighbor.chunk_id)
            continue
        added_units.append(
            _make_evidence_unit(
                candidate=RetrievedCandidate(
                    doc_id=neighbor.doc_id,
                    chunk_id=neighbor.chunk_id,
                    section_id=neighbor.section_id,
                    heading_path=neighbor.heading_path,
                    locator=_render_neighbor_locator(neighbor),
                    retrieval_score=primary_candidate.retrieval_score,
                    retrieval_rank=primary_candidate.retrieval_rank,
                ),
                chunk=neighbor,
                document=index.documents_by_id[neighbor.doc_id],
                unit_rank=start_rank + len(added_units),
                added_by_neighbor_expansion=True,
                selection_reason=f"neighbor expansion from {primary_candidate.chunk_id}",
            )
        )
        added_chunk_ids.append(neighbor.chunk_id)
    if not added_chunk_ids and not skipped_chunk_ids:
        return [], None
    return (
        added_units,
        NeighborExpansionRecord(
            anchor_chunk_id=primary_candidate.chunk_id,
            added_chunk_ids=added_chunk_ids,
            skipped_chunk_ids=skipped_chunk_ids,
        ),
    )


def _is_neighbor_expandable(primary: QueryableChunkRecord, neighbor: QueryableChunkRecord) -> bool:
    if primary.doc_id != neighbor.doc_id:
        return False
    if primary.section_id is not None and neighbor.section_id is not None:
        return primary.section_id == neighbor.section_id
    return primary.heading_path == neighbor.heading_path


def _is_same_document_group_candidate(
    primary: QueryableChunkRecord,
    other: QueryableChunkRecord,
) -> bool:
    if primary.doc_id != other.doc_id:
        return False
    if primary.section_id is not None and other.section_id is not None:
        return primary.section_id == other.section_id
    return primary.heading_path == other.heading_path


def _grouping_mode_for_units(
    *,
    interpreted_query: InterpretedQuery,
    units: list[EvidenceUnit],
) -> EvidenceGroupingMode:
    if len({unit.candidate.doc_id for unit in units}) > 1:
        return EvidenceGroupingMode.MULTI_DOCUMENT
    if any(unit.added_by_neighbor_expansion for unit in units):
        if len(units) == 2:
            return EvidenceGroupingMode.PASSAGE_WITH_NEIGHBOR
    if len(units) > 1 and (
        interpreted_query.request_type is QueryRequestType.EXPLANATION
        or interpreted_query.specificity is QuerySpecificity.SECTION_SCOPED
    ):
        return EvidenceGroupingMode.SAME_DOCUMENT_MULTI_PASSAGE
    return EvidenceGroupingMode.SINGLE_PASSAGE


def _flatten_selected_candidates(evidence_sets: list[EvidenceSet]) -> list[RetrievedCandidate]:
    selected: list[RetrievedCandidate] = []
    seen_chunk_ids: set[str] = set()
    for evidence_set in evidence_sets:
        for unit in evidence_set.evidence_units:
            if unit.added_by_neighbor_expansion:
                continue
            if unit.candidate.chunk_id in seen_chunk_ids:
                continue
            selected.append(unit.candidate)
            seen_chunk_ids.add(unit.candidate.chunk_id)
    return selected


def _finalize_decisions(
    *,
    ranked: list[SelectionDecision],
    dropped_duplicates: dict[str, SelectionDecision],
    selected_chunk_ids: set[str],
) -> list[SelectionDecision]:
    finalized: list[SelectionDecision] = []
    selected_rank = 1
    for decision in ranked:
        duplicate = dropped_duplicates.get(decision.candidate.chunk_id)
        if duplicate is not None:
            finalized.append(duplicate)
            continue
        if decision.candidate.chunk_id in selected_chunk_ids:
            finalized.append(
                decision.model_copy(
                    update={
                        "status": "selected",
                        "final_rank": selected_rank,
                    }
                )
            )
            selected_rank += 1
        else:
            finalized.append(
                decision.model_copy(
                    update={
                        "status": "dropped",
                        "drop_reason": "not_in_final_evidence_sets",
                    }
                )
            )
    return finalized


def _render_neighbor_locator(chunk: QueryableChunkRecord) -> str | None:
    if chunk.page_start is not None:
        if chunk.page_end is None or chunk.page_end == chunk.page_start:
            return f"p. {chunk.page_start}"
        return f"pp. {chunk.page_start}-{chunk.page_end}"
    if chunk.source_start_offset is not None:
        if chunk.source_end_offset is None or chunk.source_end_offset == chunk.source_start_offset:
            return f"offset {chunk.source_start_offset}"
        return f"offsets {chunk.source_start_offset}-{chunk.source_end_offset}"
    if chunk.section_id is not None:
        return f"section {chunk.section_id}"
    return None
