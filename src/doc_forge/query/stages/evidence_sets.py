"""Helpers for building evidence sets during the select stage."""

from __future__ import annotations

from doc_forge.query.contracts import (
    EvidenceGroupingMode,
    EvidenceSet,
    EvidenceUnit,
    QueryStageName,
)

STAGE_NAME = QueryStageName.SELECT


def build_evidence_set(
    *,
    evidence_set_id: str,
    grouping_mode: EvidenceGroupingMode,
    evidence_units: list[EvidenceUnit],
    purpose: str,
    coverage_notes: list[str],
    conflict_flags: list[str],
    assembly_reason: str,
) -> EvidenceSet:
    """Return a validated evidence-set object for Stage 4."""

    return EvidenceSet(
        evidence_set_id=evidence_set_id,
        grouping_mode=grouping_mode,
        evidence_units=evidence_units,
        purpose=purpose,
        coverage_notes=coverage_notes,
        conflict_flags=conflict_flags,
        assembly_reason=assembly_reason,
    )
