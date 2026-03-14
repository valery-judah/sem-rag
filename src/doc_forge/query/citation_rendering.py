"""Deterministic Stage-7 provenance-only citation rendering helpers."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from doc_forge.corpus import SourceReference
from doc_forge.identifiers import DocId

from .contracts import (
    AnswerDraft,
    AnswerMode,
    AnswerModeDecision,
    CitationBundle,
    CitationRecord,
    CitationSupportRole,
    ContextManifest,
    EvidenceSet,
    InterpretedQuery,
    SupportAssessment,
)
from .errors import QueryStageContractViolationError
from .policies import QueryPolicy

RENDERER_VERSION = "citation_rendering.deterministic.v1"


class CitationRenderingResult(BaseModel):
    """Structured Stage-7 citation rendering result."""

    model_config = ConfigDict(extra="forbid")

    citation_bundle: CitationBundle
    provenance_warnings: list[str] = Field(default_factory=lambda: [])
    renderer_version: str = Field(min_length=1)


class CitationRenderer(Protocol):
    """Provenance-only citation rendering seam."""

    def render(
        self,
        *,
        interpreted_query: InterpretedQuery,
        evidence_sets: list[EvidenceSet],
        context_manifest: ContextManifest,
        support_assessment: SupportAssessment,
        answer_mode_decision: AnswerModeDecision,
        answer_draft: AnswerDraft,
        policy: QueryPolicy,
    ) -> CitationRenderingResult:
        """Render final citations from provenance-bearing evidence only."""
        ...


class DeterministicCitationRenderer:
    """Deterministic renderer over selected evidence provenance."""

    def render(
        self,
        *,
        interpreted_query: InterpretedQuery,
        evidence_sets: list[EvidenceSet],
        context_manifest: ContextManifest,
        support_assessment: SupportAssessment,
        answer_mode_decision: AnswerModeDecision,
        answer_draft: AnswerDraft,
        policy: QueryPolicy,
    ) -> CitationRenderingResult:
        del context_manifest, support_assessment

        if not answer_draft.should_render_citations:
            return CitationRenderingResult(
                citation_bundle=CitationBundle(
                    citations=[],
                    material_doc_ids=[],
                    renderer_version=RENDERER_VERSION,
                ),
                renderer_version=RENDERER_VERSION,
            )

        grounded_ids = list(answer_draft.grounded_evidence_set_ids)
        if not grounded_ids:
            raise QueryStageContractViolationError(
                "citation rendering requires grounded evidence set ids for cited answers"
            )

        evidence_sets_by_id = {
            evidence_set.evidence_set_id: evidence_set for evidence_set in evidence_sets
        }
        expected_material_doc_ids = _expected_material_doc_ids(
            grounded_ids=grounded_ids,
            evidence_sets_by_id=evidence_sets_by_id,
        )
        citations: list[CitationRecord] = []
        material_doc_ids: list[DocId] = []
        provenance_warnings: list[str] = []
        seen_keys: set[tuple[object, ...]] = set()

        for evidence_set_id in grounded_ids:
            evidence_set = evidence_sets_by_id.get(evidence_set_id)
            if evidence_set is None:
                raise QueryStageContractViolationError(
                    "grounded evidence set "
                    f"{evidence_set_id!r} was not available for citation rendering"
                )
            for unit in sorted(
                evidence_set.evidence_units,
                key=lambda item: (
                    item.unit_rank,
                    item.candidate.doc_id,
                    item.candidate.chunk_id,
                ),
            ):
                reference = _render_source_reference(unit.source_reference, policy)
                if not _is_useful_reference(reference):
                    provenance_warnings.append(
                        f"{unit.evidence_unit_id} skipped because stored provenance was not usable"
                    )
                    continue
                dedupe_key = _citation_dedupe_key(reference)
                if dedupe_key in seen_keys:
                    continue
                seen_keys.add(dedupe_key)
                if reference.doc_id not in material_doc_ids:
                    material_doc_ids.append(reference.doc_id)
                citations.append(
                    CitationRecord(
                        evidence_set_id=evidence_set_id,
                        source_reference=reference,
                        support_role=(
                            CitationSupportRole.PRIMARY
                            if not citations
                            else CitationSupportRole.SUPPORTING
                        ),
                    )
                )

        if answer_mode_decision.answer_mode is not AnswerMode.FULL_ABSTENTION and not citations:
            raise QueryStageContractViolationError(
                "non-abstaining answers must not complete without provenance-derived citations"
            )
        if interpreted_query.requires_synthesis and expected_material_doc_ids != material_doc_ids:
            raise QueryStageContractViolationError(
                "cross-document answers must cite every materially contributing document"
            )

        return CitationRenderingResult(
            citation_bundle=CitationBundle(
                citations=citations,
                material_doc_ids=material_doc_ids,
                renderer_version=RENDERER_VERSION,
            ),
            provenance_warnings=provenance_warnings,
            renderer_version=RENDERER_VERSION,
        )


def _expected_material_doc_ids(
    *,
    grounded_ids: list[str],
    evidence_sets_by_id: dict[str, EvidenceSet],
) -> list[str]:
    doc_ids: list[DocId] = []
    for evidence_set_id in grounded_ids:
        evidence_set = evidence_sets_by_id[evidence_set_id]
        for unit in evidence_set.evidence_units:
            if unit.source_reference.doc_id not in doc_ids:
                doc_ids.append(unit.source_reference.doc_id)
    return doc_ids


def _render_source_reference(reference: SourceReference, policy: QueryPolicy) -> SourceReference:
    return SourceReference(
        doc_id=reference.doc_id,
        document_title=reference.document_title,
        snippet=reference.snippet,
        section_id=reference.section_id,
        heading_path=reference.heading_path if policy.citation_include_heading_path else None,
        page_label=reference.page_label if policy.citation_include_locator else None,
        chunk_id=reference.chunk_id,
        passage_anchor=reference.passage_anchor if policy.citation_include_locator else None,
    )


def _is_useful_reference(reference: SourceReference) -> bool:
    return bool(
        reference.page_label
        or reference.passage_anchor
        or reference.heading_path
        or reference.section_id
    )


def _citation_dedupe_key(reference: SourceReference) -> tuple[object, ...]:
    return (
        reference.doc_id,
        reference.page_label,
        tuple(reference.heading_path or ()),
        reference.passage_anchor,
        reference.section_id,
    )
