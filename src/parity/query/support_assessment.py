"""Deterministic Stage-6 support-assessment helpers."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
    ContextManifest,
    CorpusSnapshot,
    EvidenceSet,
    InterpretedQuery,
    QueryRequest,
    QueryRequestType,
    QuerySpecificity,
    SupportAssessment,
    SupportQualifierReason,
    SupportState,
    SynthesisMode,
    TrustFailureLabel,
)
from .policies import QueryPolicy


class SupportAssessmentPrecheck(BaseModel):
    """Structured precheck record used to explain Stage-6 narrowing."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    status: str = Field(min_length=1)
    support_ceiling: SupportState | None = None
    reason_codes: list[SupportQualifierReason] = Field(default_factory=list)
    summary: str | None = None
    unsupported_gaps: list[str] = Field(default_factory=list)
    conflicting_evidence_notes: list[str] = Field(default_factory=list)
    provenance_warnings: list[str] = Field(default_factory=list)


class StructuredSupportJudgment(BaseModel):
    """Normalized support-judge output before deterministic post-rules."""

    model_config = ConfigDict(extra="forbid")

    support_state: SupportState
    supported_claims: list[str] = Field(default_factory=list)
    unsupported_gaps: list[str] = Field(default_factory=list)
    conflicting_evidence_notes: list[str] = Field(default_factory=list)
    provenance_warnings: list[str] = Field(default_factory=list)
    summary: str | None = None
    judge_name: str = Field(min_length=1)


class SupportAssessmentResult(BaseModel):
    """Structured Stage-6 support-assessment output."""

    model_config = ConfigDict(extra="forbid")

    assessment: SupportAssessment
    precheck_results: list[SupportAssessmentPrecheck] = Field(default_factory=list)
    support_ceiling: SupportState | None = None
    structured_judgment: StructuredSupportJudgment | None = None


class SupportJudge(Protocol):
    """Structured support-judgment seam used inside hybrid assessment."""

    def judge(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        evidence_sets: list[EvidenceSet],
        context_manifest: ContextManifest,
        policy: QueryPolicy,
    ) -> StructuredSupportJudgment:
        """Return a structured support judgment for the assembled evidence."""
        ...


class DeterministicSupportJudge:
    """Deterministic local support judge for Stage 6 tests and default runs."""

    name = "DeterministicSupportJudge"

    def judge(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        evidence_sets: list[EvidenceSet],
        context_manifest: ContextManifest,
        policy: QueryPolicy,
    ) -> StructuredSupportJudgment:
        del request, snapshot, policy
        included_sets = _included_evidence_sets(evidence_sets, context_manifest)
        if not included_sets:
            return StructuredSupportJudgment(
                support_state=SupportState.INSUFFICIENT,
                unsupported_gaps=["No included evidence sets remain after context assembly."],
                summary="No included evidence is available to support the requested answer.",
                judge_name=self.name,
            )

        contributing_doc_ids = _contributing_doc_ids(context_manifest)
        if interpreted_query.synthesis_mode is SynthesisMode.CROSS_DOCUMENT:
            if len(contributing_doc_ids) >= 2:
                return StructuredSupportJudgment(
                    support_state=SupportState.SUFFICIENT,
                    supported_claims=[
                        "Cross-document evidence is present in the assembled context."
                    ],
                    summary="The included evidence covers the requested cross-document synthesis.",
                    judge_name=self.name,
                )
            return StructuredSupportJudgment(
                support_state=SupportState.PARTIAL,
                unsupported_gaps=[
                    "Cross-document synthesis requires support from more than one document.",
                ],
                summary=(
                    "The evidence is relevant but does not cover the requested "
                    "cross-document scope."
                ),
                judge_name=self.name,
            )

        if interpreted_query.requires_source_navigation:
            return StructuredSupportJudgment(
                support_state=SupportState.SUFFICIENT,
                supported_claims=["The assembled context contains recoverable navigation support."],
                summary="The included evidence is sufficient for a source-navigation response.",
                judge_name=self.name,
            )

        if (
            interpreted_query.specificity is QuerySpecificity.BROAD
            and interpreted_query.request_type is not QueryRequestType.FACT_LOOKUP
            and len(context_manifest.included_evidence_set_ids) == 1
        ):
            return StructuredSupportJudgment(
                support_state=SupportState.PARTIAL,
                unsupported_gaps=[
                    "The broad request may require more evidence than the current "
                    "context includes.",
                ],
                summary=(
                    "The assembled evidence is relevant but only partially covers "
                    "the broad request."
                ),
                judge_name=self.name,
            )

        if interpreted_query.request_type is QueryRequestType.UNSUPPORTED:
            return StructuredSupportJudgment(
                support_state=SupportState.INSUFFICIENT,
                unsupported_gaps=["The request depends on unsupported MVP capabilities."],
                summary="The request is outside the grounded answering scope of the MVP.",
                judge_name=self.name,
            )

        return StructuredSupportJudgment(
            support_state=SupportState.SUFFICIENT,
            supported_claims=[
                "The included evidence materially supports the requested answer shape."
            ],
            summary="The included evidence materially supports the requested answer shape.",
            judge_name=self.name,
        )


class HybridSupportAssessor:
    """Hybrid support assessor with deterministic guardrails and judge injection."""

    def __init__(self, *, judge: SupportJudge | None = None) -> None:
        self._judge = judge or DeterministicSupportJudge()

    def assess(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        evidence_sets: list[EvidenceSet],
        context_manifest: ContextManifest,
        policy: QueryPolicy,
    ) -> SupportAssessmentResult:
        prechecks: list[SupportAssessmentPrecheck] = []
        reason_codes: list[SupportQualifierReason] = []
        unsupported_gaps: list[str] = []
        conflicting_notes: list[str] = []
        provenance_warnings: list[str] = []
        support_ceiling: SupportState | None = None

        def add_precheck(record: SupportAssessmentPrecheck) -> None:
            nonlocal support_ceiling
            prechecks.append(record)
            reason_codes.extend(record.reason_codes)
            unsupported_gaps.extend(record.unsupported_gaps)
            conflicting_notes.extend(record.conflicting_evidence_notes)
            provenance_warnings.extend(record.provenance_warnings)
            if record.support_ceiling is not None:
                support_ceiling = _narrow_support_state(support_ceiling, record.support_ceiling)

        if interpreted_query.unsupported_capability_flags:
            record = SupportAssessmentPrecheck(
                name="unsupported_capability",
                status="terminated",
                support_ceiling=SupportState.INSUFFICIENT,
                reason_codes=[SupportQualifierReason.UNSUPPORTED_QUESTION_TYPE],
                summary="The interpreted query requires unsupported MVP capabilities.",
                unsupported_gaps=[
                    "The request depends on capabilities outside the grounded MVP scope."
                ],
            )
            add_precheck(record)
            return self._build_result(
                support_state=SupportState.INSUFFICIENT,
                reason_codes=reason_codes,
                summary=record.summary,
                unsupported_gaps=unsupported_gaps,
                conflicting_notes=conflicting_notes,
                provenance_warnings=provenance_warnings,
                prechecks=prechecks,
                support_ceiling=support_ceiling,
                structured_judgment=None,
            )

        if not evidence_sets or not context_manifest.context_items:
            record = SupportAssessmentPrecheck(
                name="empty_evidence",
                status="terminated",
                support_ceiling=SupportState.INSUFFICIENT,
                reason_codes=[SupportQualifierReason.NO_EVIDENCE_AVAILABLE],
                summary="No evidence is available for support assessment.",
                unsupported_gaps=["No selected evidence was included in the assembled context."],
            )
            add_precheck(record)
            return self._build_result(
                support_state=SupportState.INSUFFICIENT,
                reason_codes=reason_codes,
                summary=record.summary,
                unsupported_gaps=unsupported_gaps,
                conflicting_notes=conflicting_notes,
                provenance_warnings=provenance_warnings,
                prechecks=prechecks,
                support_ceiling=support_ceiling,
                structured_judgment=None,
            )

        if (
            policy.source_navigation_requires_locator
            and interpreted_query.requires_source_navigation
            and not _has_navigation_locator(context_manifest)
        ):
            record = SupportAssessmentPrecheck(
                name="source_navigation_locator",
                status="terminated",
                support_ceiling=SupportState.INSUFFICIENT,
                reason_codes=[SupportQualifierReason.SOURCE_NAVIGATION_LOCATOR_MISSING],
                summary="The assembled context lacks a usable source-navigation locator.",
                provenance_warnings=[
                    "The included context cannot point the user to a stable source location.",
                ],
            )
            add_precheck(record)
            return self._build_result(
                support_state=SupportState.INSUFFICIENT,
                reason_codes=reason_codes,
                summary=record.summary,
                unsupported_gaps=unsupported_gaps,
                conflicting_notes=conflicting_notes,
                provenance_warnings=provenance_warnings,
                prechecks=prechecks,
                support_ceiling=support_ceiling,
                structured_judgment=None,
            )

        if interpreted_query.synthesis_mode is SynthesisMode.CROSS_DOCUMENT:
            contributing_doc_ids = _contributing_doc_ids(context_manifest)
            if len(contributing_doc_ids) < 2:
                add_precheck(
                    SupportAssessmentPrecheck(
                        name="cross_document_coverage",
                        status="capped",
                        support_ceiling=SupportState.PARTIAL,
                        reason_codes=[SupportQualifierReason.MISSING_MATERIAL_COVERAGE],
                        summary=(
                            "The assembled context does not cover the requested "
                            "multi-document scope."
                        ),
                        unsupported_gaps=[
                            "Cross-document synthesis requires support from more "
                            "than one document.",
                        ],
                    )
                )

        conflict_flags = sorted(
            {
                flag
                for evidence_set in _included_evidence_sets(evidence_sets, context_manifest)
                for flag in evidence_set.conflict_flags
            }
        )
        if policy.conflict_caps_support_at_partial and conflict_flags:
            add_precheck(
                SupportAssessmentPrecheck(
                    name="material_conflict",
                    status="capped",
                    support_ceiling=SupportState.PARTIAL,
                    reason_codes=[SupportQualifierReason.MATERIAL_CONFLICT],
                    summary=(
                        "The included evidence contains material conflict that must remain visible."
                    ),
                    conflicting_evidence_notes=conflict_flags,
                )
            )

        if policy.provenance_weakness_caps_support_at_partial and not _has_inspectable_provenance(
            context_manifest
        ):
            add_precheck(
                SupportAssessmentPrecheck(
                    name="provenance_weakness",
                    status="capped",
                    support_ceiling=SupportState.PARTIAL,
                    reason_codes=[SupportQualifierReason.PROVENANCE_TOO_WEAK],
                    summary=(
                        "The included evidence is relevant but weakly localizable for inspection."
                    ),
                    provenance_warnings=[
                        "The assembled context lacks strong heading-path or locator provenance.",
                    ],
                )
            )

        structured_judgment = self._judge.judge(
            request=request,
            snapshot=snapshot,
            interpreted_query=interpreted_query,
            evidence_sets=evidence_sets,
            context_manifest=context_manifest,
            policy=policy,
        )
        reason_codes = _unique_reasons(reason_codes)
        unsupported_gaps = _unique_strings(
            [*unsupported_gaps, *structured_judgment.unsupported_gaps]
        )
        conflicting_notes = _unique_strings(
            [*conflicting_notes, *structured_judgment.conflicting_evidence_notes]
        )
        provenance_warnings = _unique_strings(
            [*provenance_warnings, *structured_judgment.provenance_warnings]
        )
        final_state = _narrow_support_state(structured_judgment.support_state, support_ceiling)
        if final_state is None:
            final_state = structured_judgment.support_state

        if final_state is SupportState.PARTIAL and (
            unsupported_gaps or SupportQualifierReason.MISSING_MATERIAL_COVERAGE in reason_codes
        ):
            reason_codes.append(SupportQualifierReason.SCOPE_NARROWING_REQUIRED)

        return self._build_result(
            support_state=final_state,
            reason_codes=reason_codes,
            summary=structured_judgment.summary,
            unsupported_gaps=unsupported_gaps,
            conflicting_notes=conflicting_notes,
            provenance_warnings=provenance_warnings,
            prechecks=prechecks,
            support_ceiling=support_ceiling,
            structured_judgment=structured_judgment,
        )

    def _build_result(
        self,
        *,
        support_state: SupportState,
        reason_codes: list[SupportQualifierReason],
        summary: str | None,
        unsupported_gaps: list[str],
        conflicting_notes: list[str],
        provenance_warnings: list[str],
        prechecks: list[SupportAssessmentPrecheck],
        support_ceiling: SupportState | None,
        structured_judgment: StructuredSupportJudgment | None,
    ) -> SupportAssessmentResult:
        normalized_reasons = _unique_reasons(reason_codes)
        assessment = SupportAssessment(
            support_state=support_state,
            qualifying_reason_codes=normalized_reasons,
            trust_failure_labels=_derive_trust_failure_labels(normalized_reasons, support_state),
            summary=summary,
            unsupported_gaps=_unique_strings(unsupported_gaps),
            conflicting_evidence_notes=_unique_strings(conflicting_notes),
            provenance_warnings=_unique_strings(provenance_warnings),
        )
        return SupportAssessmentResult(
            assessment=assessment,
            precheck_results=prechecks,
            support_ceiling=support_ceiling,
            structured_judgment=structured_judgment,
        )


def _included_evidence_sets(
    evidence_sets: list[EvidenceSet],
    context_manifest: ContextManifest,
) -> list[EvidenceSet]:
    included_ids = set(context_manifest.included_evidence_set_ids)
    return [
        evidence_set
        for evidence_set in evidence_sets
        if evidence_set.evidence_set_id in included_ids
    ]


def _contributing_doc_ids(context_manifest: ContextManifest) -> set[str]:
    return {
        doc_id for item in context_manifest.context_items for doc_id in item.contributing_doc_ids
    }


def _has_navigation_locator(context_manifest: ContextManifest) -> bool:
    return any(item.locators or item.heading_paths for item in context_manifest.context_items)


def _has_inspectable_provenance(context_manifest: ContextManifest) -> bool:
    return any(
        item.contributing_doc_ids or item.locators or item.heading_paths
        for item in context_manifest.context_items
    )


def _narrow_support_state(
    state: SupportState | None,
    ceiling: SupportState | None,
) -> SupportState | None:
    if state is None:
        return ceiling
    if ceiling is None:
        return state
    order = {
        SupportState.INSUFFICIENT: 0,
        SupportState.PARTIAL: 1,
        SupportState.SUFFICIENT: 2,
    }
    return state if order[state] <= order[ceiling] else ceiling


def _derive_trust_failure_labels(
    reasons: list[SupportQualifierReason],
    support_state: SupportState,
) -> list[TrustFailureLabel]:
    labels: list[TrustFailureLabel] = []
    if SupportQualifierReason.UNSUPPORTED_QUESTION_TYPE in reasons:
        labels.append(TrustFailureLabel.S1)
    if (
        SupportQualifierReason.PROVENANCE_TOO_WEAK in reasons
        or SupportQualifierReason.SOURCE_NAVIGATION_LOCATOR_MISSING in reasons
    ):
        labels.append(TrustFailureLabel.P1)
    if (
        SupportQualifierReason.MISSING_MATERIAL_COVERAGE in reasons
        and support_state is SupportState.PARTIAL
    ):
        labels.append(TrustFailureLabel.U2)
    if (
        SupportQualifierReason.NO_EVIDENCE_AVAILABLE in reasons
        and support_state is SupportState.INSUFFICIENT
    ):
        labels.append(TrustFailureLabel.A2)
    return _unique_labels(labels)


def _unique_reasons(
    reasons: list[SupportQualifierReason],
) -> list[SupportQualifierReason]:
    seen: set[SupportQualifierReason] = set()
    result: list[SupportQualifierReason] = []
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        result.append(reason)
    return result


def _unique_labels(items: list[TrustFailureLabel]) -> list[TrustFailureLabel]:
    seen: set[TrustFailureLabel] = set()
    result: list[TrustFailureLabel] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _unique_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
