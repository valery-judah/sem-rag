"""Answer-layer feasibility assessment and run evaluation for authored eval sets."""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field


class SupportStateLabel(StrEnum):
    """Question-level authored support states used by the eval case sets."""

    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED_IN_CORPUS = "UNSUPPORTED_IN_CORPUS"
    UNSUPPORTED_QUESTION_TYPE = "UNSUPPORTED_QUESTION_TYPE"
    AMBIGUOUS_OR_CONFLICTING = "AMBIGUOUS_OR_CONFLICTING"


class ExpectedBehavior(StrEnum):
    """Answer behaviors allowed by the authored answer key schema."""

    DIRECT_ANSWER_WITH_SECTION_CITATION = "direct_answer_with_section_citation"
    DIRECT_ANSWER_WITH_PAGE_CITATION = "direct_answer_with_page_citation"
    DIRECT_NAVIGATION_WITH_SECTION_CITATION = "direct_navigation_with_section_citation"
    DIRECT_NAVIGATION_WITH_PAGE_CITATION = "direct_navigation_with_page_citation"
    QUALIFIED_ANSWER_WITH_CITATION = "qualified_answer_with_citation"
    ABSTAIN_OR_STATE_INSUFFICIENT_SUPPORT = "abstain_or_state_insufficient_support"
    STATE_SCOPE_LIMITATION = "state_scope_limitation"
    SURFACE_AMBIGUITY_WITH_SOURCE_QUALIFICATION = "surface_ambiguity_with_source_qualification"
    HONEST_FAILURE_WITH_BEST_AVAILABLE_LOCATOR = "honest_failure_with_best_available_locator"


class CriterionName(StrEnum):
    """Primary answer-layer criteria from the MVP evaluation semantics."""

    SUPPORT_ALIGNMENT = "support_alignment"
    SCOPE_CONTROL = "scope_control"
    PROVENANCE_QUALITY = "provenance_quality"
    ABSTENTION_BEHAVIOR = "abstention_behavior"
    OVERALL_TRUST_OUTCOME = "overall_trust_outcome"


class CriterionFeasibility(StrEnum):
    """How strongly the current dataset can support one criterion."""

    EFFECTIVE = "effective"
    MOSTLY = "mostly"
    PARTIAL = "partial"
    WEAK = "weak"


class CriterionVerdict(StrEnum):
    """Verdict for one evaluated criterion."""

    PASS = "pass"
    PARTIAL = "partial"
    FAIL = "fail"


class TrustOutcome(StrEnum):
    """Derived answer-layer trust outcome."""

    TRUSTWORTHY = "trustworthy"
    BORDERLINE = "borderline"
    NOT_TRUSTWORTHY = "not_trustworthy"


class QuestionSpec(BaseModel):
    """Question-level ground truth for one authored eval case."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    question_class: str = Field(min_length=1)
    support_state: SupportStateLabel
    minimum_provenance: str = Field(min_length=1)
    gold_sources: list[dict[str, object]] = Field(default_factory=list)
    user_intent_note: str | None = None
    notes: str | None = None


class AuthoredCase(BaseModel):
    """One authored question record from `cases.jsonl`."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    corpus_id: str = Field(min_length=1)
    case_family: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    primary_target_failures: list[str] = Field(default_factory=list)
    secondary_target_failures: list[str] = Field(default_factory=list)
    question_spec: QuestionSpec
    authoring_notes: dict[str, object] = Field(default_factory=dict)


class GoldEvidenceSource(BaseModel):
    """Gold provenance source from `answer_keys.jsonl`."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    section_path: list[str] | None = None
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    section_anchor: str | None = None
    support_snippet: str | None = None


class AnswerKeyRecord(BaseModel):
    """Answer key metadata used for answer-layer evaluation."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    answer_type: str = Field(min_length=1)
    canonical_answer: str | list[str]
    acceptable_paraphrases: list[str] = Field(default_factory=list)
    must_include: list[str] = Field(default_factory=list)
    must_not_include: list[str] = Field(default_factory=list)
    gold_evidence_set: list[GoldEvidenceSource] = Field(default_factory=list)
    expected_behavior: ExpectedBehavior
    abstention_expected: bool
    grading_notes: str | None = None


@dataclass(frozen=True)
class AnswerLayerCaseSpec:
    """Merged case + answer key record for one authored case."""

    set_id: str
    case: AuthoredCase
    answer_key: AnswerKeyRecord


class AnswerLayerCitation(BaseModel):
    """Structured answer-layer citation contract for feasibility evaluation."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    document_title: str | None = None
    section_path: list[str] | None = None
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    section_anchor: str | None = None


class AnswerLayerRunInput(BaseModel):
    """Minimal answer-layer payload assumed by the feasibility plan."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    answer_text: str = Field(min_length=1)
    citations: list[AnswerLayerCitation] = Field(default_factory=list)


class AnswerLayerCriterionResult(BaseModel):
    """Scored result for one answer-layer criterion."""

    model_config = ConfigDict(extra="forbid")

    criterion: CriterionName
    verdict: CriterionVerdict
    rationale: str = Field(min_length=1)


class AnswerLayerRunResult(BaseModel):
    """Full answer-layer evaluation result for one system answer."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    support_alignment: AnswerLayerCriterionResult
    scope_control: AnswerLayerCriterionResult
    provenance_quality: AnswerLayerCriterionResult
    abstention_behavior: AnswerLayerCriterionResult
    overall_trust_result: AnswerLayerCriterionResult
    overall_trust_outcome: TrustOutcome
    derived_trust_outcome: bool = True


class CriterionFeasibilityAssessment(BaseModel):
    """Repository-level feasibility judgment for one criterion."""

    model_config = ConfigDict(extra="forbid")

    criterion: CriterionName
    level: CriterionFeasibility
    rationale: str = Field(min_length=1)


class CaseCriterionMatrixRow(BaseModel):
    """Per-case answer-layer feasibility view."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    set_id: str = Field(min_length=1)
    case_family: str = Field(min_length=1)
    support_state: SupportStateLabel
    question_class: str = Field(min_length=1)
    expected_behavior: ExpectedBehavior
    support_alignment: CriterionFeasibility
    scope_control: CriterionFeasibility
    provenance_quality: CriterionFeasibility
    abstention_behavior: CriterionFeasibility
    overall_trust_outcome: CriterionFeasibility


class DatasetFeasibilityAssessment(BaseModel):
    """Summary of what the current authored dataset can judge well."""

    model_config = ConfigDict(extra="forbid")

    total_cases: int = Field(ge=0)
    total_sets: int = Field(ge=0)
    source_types: list[str] = Field(default_factory=list)
    case_family_counts: dict[str, int] = Field(default_factory=dict)
    support_state_counts: dict[str, int] = Field(default_factory=dict)
    per_criterion: list[CriterionFeasibilityAssessment] = Field(default_factory=list)
    known_gaps: list[str] = Field(default_factory=list)
    minimum_additions_if_scope_expands: list[str] = Field(default_factory=list)
    case_matrix: list[CaseCriterionMatrixRow] = Field(default_factory=list)


class AnswerLayerCaseRepository:
    """Loads and indexes authored answer-layer case sets."""

    def __init__(self, cases: dict[str, AnswerLayerCaseSpec]) -> None:
        self._cases = cases

    @classmethod
    def from_repo_root(cls, repo_root: Path | None = None) -> AnswerLayerCaseRepository:
        root = repo_root or _repo_root()
        sets_dir = root / "evals" / "cases" / "sets"
        cases: dict[str, AnswerLayerCaseSpec] = {}
        for set_dir in sorted(path for path in sets_dir.iterdir() if path.is_dir()):
            cases_path = set_dir / "cases.jsonl"
            answer_keys_path = set_dir / "answer_keys.jsonl"
            if not cases_path.exists() or not answer_keys_path.exists():
                continue
            authored_cases = {case.case_id: case for case in _load_jsonl(cases_path, AuthoredCase)}
            authored_keys = {
                key.case_id: key for key in _load_jsonl(answer_keys_path, AnswerKeyRecord)
            }
            if set(authored_cases) != set(authored_keys):
                missing_keys = sorted(set(authored_cases) - set(authored_keys))
                missing_cases = sorted(set(authored_keys) - set(authored_cases))
                raise ValueError(
                    f"case/key mismatch in {set_dir.name}: "
                    f"missing_keys={missing_keys}, missing_cases={missing_cases}"
                )
            for case_id, case in authored_cases.items():
                cases[case_id] = AnswerLayerCaseSpec(
                    set_id=set_dir.name,
                    case=case,
                    answer_key=authored_keys[case_id],
                )
        return cls(cases)

    def get(self, case_id: str) -> AnswerLayerCaseSpec:
        try:
            return self._cases[case_id]
        except KeyError as exc:
            raise KeyError(f"unknown eval case_id {case_id!r}") from exc

    def values(self) -> list[AnswerLayerCaseSpec]:
        return [self._cases[case_id] for case_id in sorted(self._cases)]

    def __len__(self) -> int:
        return len(self._cases)


class AnswerLayerFeasibilityAssessor:
    """Builds the repository-level answer-layer feasibility summary."""

    def assess(self, repository: AnswerLayerCaseRepository) -> DatasetFeasibilityAssessment:
        cases = repository.values()
        case_family_counts = _count_by(cases, key=lambda item: item.case.case_family)
        support_state_counts = _count_by(
            cases, key=lambda item: item.case.question_spec.support_state.value
        )
        source_types = sorted({item.case.source_type for item in cases})
        matrix = [self._build_matrix_row(case_spec) for case_spec in cases]
        return DatasetFeasibilityAssessment(
            total_cases=len(cases),
            total_sets=len({item.set_id for item in cases}),
            source_types=source_types,
            case_family_counts=case_family_counts,
            support_state_counts=support_state_counts,
            per_criterion=[
                CriterionFeasibilityAssessment(
                    criterion=CriterionName.SUPPORT_ALIGNMENT,
                    level=CriterionFeasibility.EFFECTIVE,
                    rationale=(
                        "Current answer keys expose canonical answers, acceptable paraphrases, "
                        "must-include phrases, must-not-include phrases, and gold evidence."
                    ),
                ),
                CriterionFeasibilityAssessment(
                    criterion=CriterionName.ABSTENTION_BEHAVIOR,
                    level=CriterionFeasibility.EFFECTIVE,
                    rationale=(
                        "Every answer key declares expected behavior and whether abstention is "
                        "expected, which is enough for stable answer-layer judging."
                    ),
                ),
                CriterionFeasibilityAssessment(
                    criterion=CriterionName.SCOPE_CONTROL,
                    level=CriterionFeasibility.MOSTLY,
                    rationale=(
                        "Partial-support, unsupported, and ambiguity slices encode qualification "
                        "or refusal requirements clearly; supported direct-answer slices are a "
                        "bit weaker when overbroad answers remain partly correct."
                    ),
                ),
                CriterionFeasibilityAssessment(
                    criterion=CriterionName.PROVENANCE_QUALITY,
                    level=CriterionFeasibility.PARTIAL,
                    rationale=(
                        "Gold evidence sets make structured citation checks possible, but the "
                        "current assets do not encode enough alternative-localizer or "
                        "partial-credit policy to support robust citation grading."
                    ),
                ),
                CriterionFeasibilityAssessment(
                    criterion=CriterionName.OVERALL_TRUST_OUTCOME,
                    level=CriterionFeasibility.WEAK,
                    rationale=(
                        "Trust outcome can be derived conservatively from the other criteria, "
                        "but it is not gold-labeled directly in the current answer keys."
                    ),
                ),
            ],
            known_gaps=[
                "The dataset is Markdown-only, so it does not validate the mixed-format MVP contract yet.",
                "Overall trust outcome and primary failure labels are rubric-derived, not dataset-native.",
                "Citation grading lacks explicit acceptable alternates, breadth tolerance, and partial-credit rules.",
                "The current assets cannot judge retrieval quality, context assembly quality, or secondary-cause attribution.",
            ],
            minimum_additions_if_scope_expands=[
                "Add gold_overall_trust_outcome and gold_primary_failure fields to answer keys.",
                "Add acceptable_citation_variants with coarse-vs-precise provenance rules.",
                "Add at least one PDF-backed set and one mixed-format synthesis set.",
                "Add citation grading rules for document mismatch, wrong localizer, overly broad citation, missing contributing source, and coarse-but-honest provenance.",
            ],
            case_matrix=matrix,
        )

    def _build_matrix_row(self, case_spec: AnswerLayerCaseSpec) -> CaseCriterionMatrixRow:
        expected_behavior = case_spec.answer_key.expected_behavior
        support_state = case_spec.case.question_spec.support_state
        if support_state in {
            SupportStateLabel.PARTIALLY_SUPPORTED,
            SupportStateLabel.UNSUPPORTED_IN_CORPUS,
            SupportStateLabel.UNSUPPORTED_QUESTION_TYPE,
            SupportStateLabel.AMBIGUOUS_OR_CONFLICTING,
        }:
            scope_feasibility = CriterionFeasibility.EFFECTIVE
        else:
            scope_feasibility = CriterionFeasibility.MOSTLY

        return CaseCriterionMatrixRow(
            case_id=case_spec.case.case_id,
            set_id=case_spec.set_id,
            case_family=case_spec.case.case_family,
            support_state=support_state,
            question_class=case_spec.case.question_spec.question_class,
            expected_behavior=expected_behavior,
            support_alignment=CriterionFeasibility.EFFECTIVE,
            scope_control=scope_feasibility,
            provenance_quality=CriterionFeasibility.PARTIAL,
            abstention_behavior=CriterionFeasibility.EFFECTIVE,
            overall_trust_outcome=CriterionFeasibility.WEAK,
        )


class AnswerLayerEvaluator:
    """Evaluates one answer-layer run against authored eval keys."""

    def __init__(self, repository: AnswerLayerCaseRepository) -> None:
        self._repository = repository

    def evaluate(self, run: AnswerLayerRunInput) -> AnswerLayerRunResult:
        case_spec = self._repository.get(run.case_id)
        support_alignment = _evaluate_support_alignment(case_spec, run)
        abstention_behavior = _evaluate_abstention_behavior(case_spec, run, support_alignment)
        scope_control = _evaluate_scope_control(
            case_spec,
            run,
            support_alignment=support_alignment,
            abstention_behavior=abstention_behavior,
        )
        provenance_quality = _evaluate_provenance_quality(case_spec, run)
        overall_trust_outcome, trust_result = _derive_overall_trust(
            case_spec=case_spec,
            support_alignment=support_alignment,
            scope_control=scope_control,
            provenance_quality=provenance_quality,
            abstention_behavior=abstention_behavior,
        )
        return AnswerLayerRunResult(
            case_id=run.case_id,
            support_alignment=support_alignment,
            scope_control=scope_control,
            provenance_quality=provenance_quality,
            abstention_behavior=abstention_behavior,
            overall_trust_result=trust_result,
            overall_trust_outcome=overall_trust_outcome,
        )


def _evaluate_support_alignment(
    case_spec: AnswerLayerCaseSpec,
    run: AnswerLayerRunInput,
) -> AnswerLayerCriterionResult:
    normalized_answer = _normalize_text(run.answer_text)
    key = case_spec.answer_key
    missing_required = [
        phrase for phrase in key.must_include if not _contains_phrase(normalized_answer, phrase)
    ]
    forbidden_present = [
        phrase for phrase in key.must_not_include if _contains_phrase(normalized_answer, phrase)
    ]
    canonical_variants = _canonical_variants(key)
    matches_variant = any(
        normalized_answer == _normalize_text(variant) for variant in canonical_variants
    )

    if forbidden_present:
        return AnswerLayerCriterionResult(
            criterion=CriterionName.SUPPORT_ALIGNMENT,
            verdict=CriterionVerdict.FAIL,
            rationale=(
                "Answer includes authored must-not-include content: "
                + ", ".join(sorted(forbidden_present))
            ),
        )
    if missing_required and not matches_variant:
        return AnswerLayerCriterionResult(
            criterion=CriterionName.SUPPORT_ALIGNMENT,
            verdict=CriterionVerdict.FAIL,
            rationale=(
                "Answer is missing authored must-include concepts: "
                + ", ".join(sorted(missing_required))
            ),
        )

    rationale = (
        "Answer matches an authored canonical/paraphrase variant."
        if matches_variant
        else "Answer preserves all authored must-include concepts and avoids forbidden content."
    )
    return AnswerLayerCriterionResult(
        criterion=CriterionName.SUPPORT_ALIGNMENT,
        verdict=CriterionVerdict.PASS,
        rationale=rationale,
    )


def _evaluate_abstention_behavior(
    case_spec: AnswerLayerCaseSpec,
    run: AnswerLayerRunInput,
    support_alignment: AnswerLayerCriterionResult,
) -> AnswerLayerCriterionResult:
    key = case_spec.answer_key
    normalized_answer = _normalize_text(run.answer_text)
    has_abstention_signal = any(
        _contains_phrase(normalized_answer, phrase) for phrase in _ABSTENTION_MARKERS
    )
    has_refusal_signal = any(
        _contains_phrase(normalized_answer, phrase) for phrase in _STRONG_REFUSAL_MARKERS
    )

    if key.abstention_expected:
        if has_abstention_signal or support_alignment.verdict is CriterionVerdict.PASS:
            return AnswerLayerCriterionResult(
                criterion=CriterionName.ABSTENTION_BEHAVIOR,
                verdict=CriterionVerdict.PASS,
                rationale=(
                    "Case expects abstention or explicit limitation, and the answer stays on "
                    "that posture."
                ),
            )
        return AnswerLayerCriterionResult(
            criterion=CriterionName.ABSTENTION_BEHAVIOR,
            verdict=CriterionVerdict.FAIL,
            rationale=(
                "Case expects abstention or explicit limitation, but the answer does not make "
                "that boundary visible."
            ),
        )

    if has_refusal_signal and support_alignment.verdict is not CriterionVerdict.PASS:
        return AnswerLayerCriterionResult(
            criterion=CriterionName.ABSTENTION_BEHAVIOR,
            verdict=CriterionVerdict.FAIL,
            rationale=(
                "Case is answerable at the answer layer, but the response looks like an "
                "unnecessary refusal."
            ),
        )

    return AnswerLayerCriterionResult(
        criterion=CriterionName.ABSTENTION_BEHAVIOR,
        verdict=CriterionVerdict.PASS,
        rationale="Answer posture is compatible with the authored abstention expectation.",
    )


def _evaluate_scope_control(
    case_spec: AnswerLayerCaseSpec,
    run: AnswerLayerRunInput,
    *,
    support_alignment: AnswerLayerCriterionResult,
    abstention_behavior: AnswerLayerCriterionResult,
) -> AnswerLayerCriterionResult:
    expected_behavior = case_spec.answer_key.expected_behavior
    normalized_answer = _normalize_text(run.answer_text)

    if support_alignment.verdict is CriterionVerdict.FAIL:
        return AnswerLayerCriterionResult(
            criterion=CriterionName.SCOPE_CONTROL,
            verdict=CriterionVerdict.FAIL,
            rationale=(
                "Support-alignment failure indicates the answer exceeded the authored support "
                "boundary for this case."
            ),
        )
    if abstention_behavior.verdict is CriterionVerdict.FAIL:
        return AnswerLayerCriterionResult(
            criterion=CriterionName.SCOPE_CONTROL,
            verdict=CriterionVerdict.FAIL,
            rationale="The answer/admit-or-abstain decision does not match the authored scope.",
        )

    if expected_behavior is ExpectedBehavior.QUALIFIED_ANSWER_WITH_CITATION:
        if any(_contains_phrase(normalized_answer, marker) for marker in _QUALIFICATION_MARKERS):
            return AnswerLayerCriterionResult(
                criterion=CriterionName.SCOPE_CONTROL,
                verdict=CriterionVerdict.PASS,
                rationale="Answer visibly qualifies the supported portion instead of overstating.",
            )
        return AnswerLayerCriterionResult(
            criterion=CriterionName.SCOPE_CONTROL,
            verdict=CriterionVerdict.FAIL,
            rationale="Partial-support case needs visible qualification, but the answer reads flat.",
        )

    if expected_behavior is ExpectedBehavior.SURFACE_AMBIGUITY_WITH_SOURCE_QUALIFICATION:
        if any(_contains_phrase(normalized_answer, marker) for marker in _AMBIGUITY_MARKERS):
            return AnswerLayerCriterionResult(
                criterion=CriterionName.SCOPE_CONTROL,
                verdict=CriterionVerdict.PASS,
                rationale="Answer surfaces the conflict or unresolved state instead of collapsing it.",
            )
        return AnswerLayerCriterionResult(
            criterion=CriterionName.SCOPE_CONTROL,
            verdict=CriterionVerdict.FAIL,
            rationale=(
                "Ambiguous/conflicting case requires visible tension handling, but the answer "
                "does not surface it."
            ),
        )

    if expected_behavior in {
        ExpectedBehavior.ABSTAIN_OR_STATE_INSUFFICIENT_SUPPORT,
        ExpectedBehavior.STATE_SCOPE_LIMITATION,
        ExpectedBehavior.HONEST_FAILURE_WITH_BEST_AVAILABLE_LOCATOR,
    }:
        return AnswerLayerCriterionResult(
            criterion=CriterionName.SCOPE_CONTROL,
            verdict=CriterionVerdict.PASS,
            rationale="Unsupported or out-of-scope case stays within the authored refusal boundary.",
        )

    return AnswerLayerCriterionResult(
        criterion=CriterionName.SCOPE_CONTROL,
        verdict=CriterionVerdict.PASS,
        rationale="Answer stays within the authored scope for a direct-answer case.",
    )


def _evaluate_provenance_quality(
    case_spec: AnswerLayerCaseSpec,
    run: AnswerLayerRunInput,
) -> AnswerLayerCriterionResult:
    gold_sources = case_spec.answer_key.gold_evidence_set
    citations = run.citations
    if not citations:
        verdict = CriterionVerdict.PARTIAL
        rationale = "Answer is materially safe, but no structured citations were provided."
        return AnswerLayerCriterionResult(
            criterion=CriterionName.PROVENANCE_QUALITY,
            verdict=verdict,
            rationale=rationale,
        )

    per_gold_matches = [
        _best_match_for_gold(gold_source, citations) for gold_source in gold_sources
    ]
    if any(
        match in {"wrong_document", "wrong_region", "false_precision"} for match in per_gold_matches
    ):
        return AnswerLayerCriterionResult(
            criterion=CriterionName.PROVENANCE_QUALITY,
            verdict=CriterionVerdict.FAIL,
            rationale=(
                "At least one citation points to the wrong document/region or implies unsupported "
                "precision."
            ),
        )

    requires_multi_source_coverage = (
        case_spec.case.question_spec.question_class == "multi_source_synthesis"
        or case_spec.case.question_spec.support_state is SupportStateLabel.AMBIGUOUS_OR_CONFLICTING
    )
    if "missing" in per_gold_matches:
        verdict = (
            CriterionVerdict.FAIL if requires_multi_source_coverage else CriterionVerdict.PARTIAL
        )
        rationale = (
            "Case requires all materially contributing sources, but one or more gold sources are missing."
            if verdict is CriterionVerdict.FAIL
            else "Some relevant gold support is uncited, so provenance remains only partially inspectable."
        )
        return AnswerLayerCriterionResult(
            criterion=CriterionName.PROVENANCE_QUALITY,
            verdict=verdict,
            rationale=rationale,
        )

    if any(match in {"doc_only", "coarse"} for match in per_gold_matches):
        return AnswerLayerCriterionResult(
            criterion=CriterionName.PROVENANCE_QUALITY,
            verdict=CriterionVerdict.PARTIAL,
            rationale=(
                "Citations point to the right source material, but the localizer is broader than the "
                "current answer keys can score as a full provenance pass."
            ),
        )

    return AnswerLayerCriterionResult(
        criterion=CriterionName.PROVENANCE_QUALITY,
        verdict=CriterionVerdict.PASS,
        rationale="Citations match the gold evidence set with inspectable localizers.",
    )


def _derive_overall_trust(
    *,
    case_spec: AnswerLayerCaseSpec,
    support_alignment: AnswerLayerCriterionResult,
    scope_control: AnswerLayerCriterionResult,
    provenance_quality: AnswerLayerCriterionResult,
    abstention_behavior: AnswerLayerCriterionResult,
) -> tuple[TrustOutcome, AnswerLayerCriterionResult]:
    del case_spec

    if any(
        result.verdict is CriterionVerdict.FAIL
        for result in (support_alignment, scope_control, abstention_behavior)
    ):
        rationale = (
            "Derived trust outcome is not trustworthy because the answer crossed a support or "
            "answer-mode boundary."
        )
        return (
            TrustOutcome.NOT_TRUSTWORTHY,
            AnswerLayerCriterionResult(
                criterion=CriterionName.OVERALL_TRUST_OUTCOME,
                verdict=CriterionVerdict.FAIL,
                rationale=rationale,
            ),
        )

    if provenance_quality.verdict is CriterionVerdict.FAIL:
        return (
            TrustOutcome.NOT_TRUSTWORTHY,
            AnswerLayerCriterionResult(
                criterion=CriterionName.OVERALL_TRUST_OUTCOME,
                verdict=CriterionVerdict.FAIL,
                rationale=(
                    "Derived trust outcome is not trustworthy because provenance is materially false "
                    "or points to the wrong region."
                ),
            ),
        )

    if provenance_quality.verdict is CriterionVerdict.PARTIAL:
        return (
            TrustOutcome.BORDERLINE,
            AnswerLayerCriterionResult(
                criterion=CriterionName.OVERALL_TRUST_OUTCOME,
                verdict=CriterionVerdict.PARTIAL,
                rationale=(
                    "Derived trust outcome is borderline: the answer is materially safe, but the "
                    "citations are weaker than a full pass."
                ),
            ),
        )

    return (
        TrustOutcome.TRUSTWORTHY,
        AnswerLayerCriterionResult(
            criterion=CriterionName.OVERALL_TRUST_OUTCOME,
            verdict=CriterionVerdict.PASS,
            rationale=(
                "Derived trust outcome is trustworthy because support, scope, abstention, and "
                "provenance all pass at the answer layer."
            ),
        ),
    )


def _best_match_for_gold(
    gold_source: GoldEvidenceSource, citations: list[AnswerLayerCitation]
) -> str:
    same_doc_citations = [
        citation for citation in citations if citation.doc_id == gold_source.doc_id
    ]
    if not same_doc_citations:
        return "missing"

    matches = [_match_gold_source(gold_source, citation) for citation in same_doc_citations]
    for preferred in ("exact", "coarse", "doc_only", "false_precision", "wrong_region"):
        if preferred in matches:
            return preferred
    return "wrong_document"


def _match_gold_source(gold_source: GoldEvidenceSource, citation: AnswerLayerCitation) -> str:
    if citation.doc_id != gold_source.doc_id:
        return "wrong_document"

    if gold_source.section_path is not None:
        if citation.section_path is None:
            return "doc_only"
        if citation.section_path == gold_source.section_path:
            return "exact"
        if _is_prefix(citation.section_path, gold_source.section_path):
            return "coarse"
        if _is_prefix(gold_source.section_path, citation.section_path):
            return "false_precision"
        return "wrong_region"

    if gold_source.page_start is not None:
        if citation.page_start is None:
            return "doc_only"
        page_end = gold_source.page_end or gold_source.page_start
        if gold_source.page_start <= citation.page_start <= page_end:
            return "exact"
        return "wrong_region"

    if gold_source.section_anchor is not None:
        if citation.section_anchor is None:
            return "doc_only"
        return "exact" if citation.section_anchor == gold_source.section_anchor else "wrong_region"

    return "doc_only"


def _canonical_variants(key: AnswerKeyRecord) -> list[str]:
    variants: list[str] = []
    if isinstance(key.canonical_answer, list):
        variants.append(" ".join(key.canonical_answer))
    else:
        variants.append(key.canonical_answer)
    variants.extend(key.acceptable_paraphrases)
    return variants


ModelT = TypeVar("ModelT", bound=BaseModel)


def _load_jsonl(path: Path, model_type: type[ModelT]) -> list[ModelT]:
    rows: list[ModelT] = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        rows.append(model_type.model_validate(json.loads(stripped)))
    return rows


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _count_by(
    cases: list[AnswerLayerCaseSpec],
    *,
    key: Callable[[AnswerLayerCaseSpec], str],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for case in cases:
        value = key(case)
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).lower()
    normalized = normalized.replace("’", "'")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return " ".join(normalized.split())


def _contains_phrase(answer_text: str, phrase: str) -> bool:
    return _normalize_text(phrase) in answer_text


def _is_prefix(prefix: list[str], target: list[str]) -> bool:
    if len(prefix) >= len(target):
        return False
    return prefix == target[: len(prefix)]


_ABSTENTION_MARKERS = (
    "cannot answer",
    "can t answer",
    "does not provide",
    "not available",
    "cannot be answered",
    "out of scope",
    "not reproduced",
    "omitted",
    "not transcribed",
    "not written out",
    "not ratified",
    "deferred",
    "unresolved",
    "not enough evidence",
    "not enough support",
    "not in this file",
    "does not contain",
    "does not support",
    "cannot recover",
)

_STRONG_REFUSAL_MARKERS = (
    "cannot answer",
    "can t answer",
    "cannot be answered",
    "out of scope",
    "not enough evidence",
    "not enough support",
    "insufficient support",
)

_QUALIFICATION_MARKERS = (
    "but",
    "however",
    "only",
    "limited",
    "conditional",
    "remain",
    "unresolved",
    "mixed",
    "not establish",
    "do not establish",
)

_AMBIGUITY_MARKERS = (
    "conflict",
    "unresolved",
    "not settled",
    "mixed",
    "tradeoff",
    "while",
    "sometimes",
    "often",
    "both",
)
