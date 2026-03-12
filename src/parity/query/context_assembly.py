"""Deterministic Stage-5 context assembly helpers."""

from __future__ import annotations

from math import ceil
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
    ContextItem,
    ContextManifest,
    CorpusSnapshot,
    EvidenceSet,
    EvidenceUnit,
    InterpretedQuery,
    QueryRequest,
)
from .policies import QueryPolicy


class ContextAssemblyDecision(BaseModel):
    """Structured include/drop decision for one evidence set."""

    model_config = ConfigDict(extra="forbid")

    evidence_set_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    assembly_rank: int | None = Field(default=None, ge=1)
    estimated_token_count: int = Field(ge=0)
    reason: str = Field(min_length=1)


class ContextAssemblyResult(BaseModel):
    """Structured Stage-5 output consumed by the context stage."""

    model_config = ConfigDict(extra="forbid")

    manifest: ContextManifest
    decisions: list[ContextAssemblyDecision] = Field(default_factory=list)


class ContextAssembler(Protocol):
    """Context-assembly seam for deterministic evidence rendering."""

    def assemble(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        evidence_sets: list[EvidenceSet],
        policy: QueryPolicy,
    ) -> ContextAssemblyResult:
        """Return a deterministic context manifest over selected evidence sets."""


class DeterministicContextAssembler:
    """Deterministic Stage-5 assembler over Stage-4 evidence sets."""

    def assemble(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        evidence_sets: list[EvidenceSet],
        policy: QueryPolicy,
    ) -> ContextAssemblyResult:
        del request, snapshot, interpreted_query

        ordered_ids = [evidence_set.evidence_set_id for evidence_set in evidence_sets]
        included_ids: list[str] = []
        dropped_ids: list[str] = []
        inclusion_reasons: dict[str, str] = {}
        exclusion_reasons: dict[str, str] = {}
        context_items: list[ContextItem] = []
        decisions: list[ContextAssemblyDecision] = []
        duplicate_suppression_notes: list[str] = []
        seen_rendered_texts: set[str] = set()
        used_budget = 0

        for evidence_set in evidence_sets:
            item, notes = _render_context_item(
                evidence_set=evidence_set,
                assembly_rank=len(context_items) + 1,
            )
            duplicate_suppression_notes.extend(notes)
            if item is None:
                dropped_ids.append(evidence_set.evidence_set_id)
                exclusion_reasons[evidence_set.evidence_set_id] = "dropped_empty_rendering"
                decisions.append(
                    ContextAssemblyDecision(
                        evidence_set_id=evidence_set.evidence_set_id,
                        status="dropped",
                        estimated_token_count=0,
                        reason="dropped_empty_rendering",
                    )
                )
                continue
            if item.rendered_text in seen_rendered_texts:
                dropped_ids.append(evidence_set.evidence_set_id)
                exclusion_reasons[evidence_set.evidence_set_id] = "dropped_duplicate_rendering"
                duplicate_suppression_notes.append(
                    f"{evidence_set.evidence_set_id} dropped because rendered context "
                    "duplicated an earlier item"
                )
                decisions.append(
                    ContextAssemblyDecision(
                        evidence_set_id=evidence_set.evidence_set_id,
                        status="dropped",
                        estimated_token_count=item.estimated_token_count,
                        reason="dropped_duplicate_rendering",
                    )
                )
                continue
            if used_budget + item.estimated_token_count > policy.context_token_budget:
                dropped_ids.append(evidence_set.evidence_set_id)
                exclusion_reasons[evidence_set.evidence_set_id] = "dropped_over_budget"
                decisions.append(
                    ContextAssemblyDecision(
                        evidence_set_id=evidence_set.evidence_set_id,
                        status="dropped",
                        estimated_token_count=item.estimated_token_count,
                        reason="dropped_over_budget",
                    )
                )
                continue
            reason = (
                "included_primary_support_priority"
                if not included_ids
                else "included_within_budget"
            )
            included_ids.append(evidence_set.evidence_set_id)
            inclusion_reasons[evidence_set.evidence_set_id] = reason
            context_items.append(item)
            used_budget += item.estimated_token_count
            seen_rendered_texts.add(item.rendered_text)
            decisions.append(
                ContextAssemblyDecision(
                    evidence_set_id=evidence_set.evidence_set_id,
                    status="included",
                    assembly_rank=item.assembly_rank,
                    estimated_token_count=item.estimated_token_count,
                    reason=reason,
                )
            )

        manifest = ContextManifest(
            ordered_evidence_set_ids=ordered_ids,
            included_evidence_set_ids=included_ids,
            dropped_evidence_set_ids=dropped_ids,
            inclusion_reasons=inclusion_reasons,
            exclusion_reasons=exclusion_reasons,
            token_budget=policy.context_token_budget,
            token_budget_used=used_budget,
            context_items=context_items,
            duplicate_suppression_notes=duplicate_suppression_notes,
        )
        return ContextAssemblyResult(manifest=manifest, decisions=decisions)


def _render_context_item(
    *,
    evidence_set: EvidenceSet,
    assembly_rank: int,
) -> tuple[ContextItem | None, list[str]]:
    units = sorted(
        evidence_set.evidence_units,
        key=lambda unit: (
            unit.unit_rank,
            unit.candidate.doc_id,
            unit.candidate.chunk_id,
        ),
    )
    if not units:
        return None, []

    duplicate_notes: list[str] = []
    rendered_lines: list[str] = []
    contributing_doc_ids: list[str] = []
    heading_paths: list[list[str]] = []
    locators: list[str] = []
    seen_unit_keys: set[tuple[str, str | None, str]] = set()

    primary = units[0]
    title = primary.source_reference.document_title
    heading = _render_heading_path(primary)
    rendered_lines.append(f"{title} | {evidence_set.purpose} | {heading}")
    is_multi_document = len({unit.source_reference.doc_id for unit in units}) > 1

    for unit in units:
        unit_key = (
            unit.source_reference.snippet.strip(),
            unit.source_reference.page_label or unit.source_reference.passage_anchor,
            unit.source_reference.doc_id,
        )
        if unit is not primary and unit_key in seen_unit_keys:
            duplicate_notes.append(
                f"{unit.evidence_unit_id} suppressed during context assembly as repeated support"
            )
            continue
        seen_unit_keys.add(unit_key)
        if unit.source_reference.doc_id not in contributing_doc_ids:
            contributing_doc_ids.append(unit.source_reference.doc_id)
        if (
            unit.source_reference.heading_path
            and unit.source_reference.heading_path not in heading_paths
        ):
            heading_paths.append(unit.source_reference.heading_path)
        locator = unit.source_reference.page_label or unit.source_reference.passage_anchor
        if locator and locator not in locators:
            locators.append(locator)
        snippet = unit.source_reference.snippet.strip()
        if not snippet:
            continue
        locator_prefix = f"[{locator}] " if locator else ""
        if is_multi_document:
            rendered_lines.append(
                f"{locator_prefix}{unit.source_reference.document_title}: {snippet}"
            )
        else:
            rendered_lines.append(f"{locator_prefix}{snippet}")

    rendered_text = "\n".join(line for line in rendered_lines if line.strip()).strip()
    if len(rendered_lines) <= 1 or not rendered_text:
        return None, duplicate_notes
    return (
        ContextItem(
            evidence_set_id=evidence_set.evidence_set_id,
            assembly_rank=assembly_rank,
            rendered_text=rendered_text,
            contributing_doc_ids=contributing_doc_ids,
            heading_paths=heading_paths,
            locators=locators,
            estimated_token_count=_estimate_token_count(rendered_text),
        ),
        duplicate_notes,
    )


def _render_heading_path(unit: EvidenceUnit) -> str:
    if unit.source_reference.heading_path:
        return " > ".join(unit.source_reference.heading_path)
    if unit.source_reference.section_id:
        return f"section {unit.source_reference.section_id}"
    return "unscoped support"


def _estimate_token_count(text: str) -> int:
    return max(1, ceil(len(text) / 4))
