from __future__ import annotations

from pathlib import Path

from doc_forge.evaluation import (
    AnswerLayerCaseRepository,
    AnswerLayerCitation,
    AnswerLayerEvaluator,
    AnswerLayerFeasibilityAssessor,
    AnswerLayerRunInput,
    CriterionFeasibility,
    CriterionName,
    CriterionVerdict,
    TrustOutcome,
)
from doc_forge.evaluation.identifiers import parse_corpus_id

REPO_ROOT = Path(__file__).resolve().parents[2]


def _repository() -> AnswerLayerCaseRepository:
    return AnswerLayerCaseRepository.from_repo_root(REPO_ROOT)


def _citation(*, doc_id: str, section_path: list[str]) -> AnswerLayerCitation:
    return AnswerLayerCitation(doc_id=parse_corpus_id(doc_id), section_path=section_path)


def test_assessment_summarizes_current_authored_dataset() -> None:
    repository = _repository()

    assessment = AnswerLayerFeasibilityAssessor().assess(repository)

    levels = {item.criterion: item.level for item in assessment.per_criterion}

    assert assessment.total_cases == 98
    assert assessment.total_sets == 10
    assert assessment.source_types == ["markdown"]
    assert assessment.case_family_counts["unsupported_in_corpus"] == 12
    assert assessment.support_state_counts["SUPPORTED"] == 46
    assert levels[CriterionName.SUPPORT_ALIGNMENT] is CriterionFeasibility.EFFECTIVE
    assert levels[CriterionName.SCOPE_CONTROL] is CriterionFeasibility.MOSTLY
    assert levels[CriterionName.PROVENANCE_QUALITY] is CriterionFeasibility.PARTIAL
    assert levels[CriterionName.OVERALL_TRUST_OUTCOME] is CriterionFeasibility.WEAK
    assert any("Markdown-only" in gap for gap in assessment.known_gaps)


def test_supported_lookup_answer_with_exact_citation_is_trustworthy() -> None:
    repository = _repository()
    evaluator = AnswerLayerEvaluator(repository)
    case_spec = repository.get("lookup_rn1_001")

    result = evaluator.evaluate(
        AnswerLayerRunInput(
            case_id="lookup_rn1_001",
            answer_text="under 2.5 seconds median end-to-end latency",
            citations=[
                _citation(
                    doc_id="research-notes-1",
                    section_path=case_spec.answer_key.gold_evidence_set[0].section_path or [],
                )
            ],
        )
    )

    assert result.support_alignment.verdict is CriterionVerdict.PASS
    assert result.scope_control.verdict is CriterionVerdict.PASS
    assert result.abstention_behavior.verdict is CriterionVerdict.PASS
    assert result.provenance_quality.verdict is CriterionVerdict.PASS
    assert result.overall_trust_outcome is TrustOutcome.TRUSTWORTHY


def test_unsupported_in_corpus_abstention_with_gold_citations_is_trustworthy() -> None:
    repository = _repository()
    evaluator = AnswerLayerEvaluator(repository)
    case_spec = repository.get("unsup_rn2_001")

    result = evaluator.evaluate(
        AnswerLayerRunInput(
            case_id="unsup_rn2_001",
            answer_text=(
                "The file does not provide those exact heatmap values. It says the latency "
                "heatmap was not reproduced in the Markdown export and that the specific cell "
                "values were not transcribed here."
            ),
            citations=[
                _citation(doc_id=source.doc_id, section_path=source.section_path or [])
                for source in case_spec.answer_key.gold_evidence_set
            ],
        )
    )

    assert result.support_alignment.verdict is CriterionVerdict.PASS
    assert result.abstention_behavior.verdict is CriterionVerdict.PASS
    assert result.scope_control.verdict is CriterionVerdict.PASS
    assert result.provenance_quality.verdict is CriterionVerdict.PASS
    assert result.overall_trust_outcome is TrustOutcome.TRUSTWORTHY


def test_unsupported_question_type_answer_with_invented_detail_is_not_trustworthy() -> None:
    repository = _repository()
    evaluator = AnswerLayerEvaluator(repository)

    result = evaluator.evaluate(
        AnswerLayerRunInput(
            case_id="uqt_rn2_001",
            answer_text=(
                "The exact heatmap values are available: the worst cell for top-4 was 812 ms, "
                "which the screenshot showed clearly."
            ),
            citations=[
                _citation(
                    doc_id="research-notes-2",
                    section_path=[
                        "9. Dashboard References Not Included in Text Export",
                        "9.1 Latency heatmap",
                    ],
                )
            ],
        )
    )

    assert result.support_alignment.verdict is CriterionVerdict.FAIL
    assert result.scope_control.verdict is CriterionVerdict.FAIL
    assert result.overall_trust_outcome is TrustOutcome.NOT_TRUSTWORTHY


def test_missing_citations_make_otherwise_safe_answer_borderline() -> None:
    repository = _repository()
    evaluator = AnswerLayerEvaluator(repository)

    result = evaluator.evaluate(
        AnswerLayerRunInput(
            case_id="lookup_rn1_001",
            answer_text="under 2.5 seconds median end-to-end latency",
            citations=[],
        )
    )

    assert result.support_alignment.verdict is CriterionVerdict.PASS
    assert result.provenance_quality.verdict is CriterionVerdict.PARTIAL
    assert result.overall_trust_outcome is TrustOutcome.BORDERLINE


def test_ambiguous_case_requires_visible_conflict_and_all_gold_sources() -> None:
    repository = _repository()
    evaluator = AnswerLayerEvaluator(repository)
    case_spec = repository.get("conflict_rn2_001")

    result = evaluator.evaluate(
        AnswerLayerRunInput(
            case_id="conflict_rn2_001",
            answer_text=(
                "The notes do not settle one best synthesis budget: top-8 sometimes scored "
                "best for completeness offline, top-6 often produced better human trust "
                "outcomes, and the conflict was left unresolved."
            ),
            citations=[
                _citation(doc_id=source.doc_id, section_path=source.section_path or [])
                for source in case_spec.answer_key.gold_evidence_set
            ],
        )
    )

    assert result.support_alignment.verdict is CriterionVerdict.PASS
    assert result.scope_control.verdict is CriterionVerdict.PASS
    assert result.provenance_quality.verdict is CriterionVerdict.PASS
    assert result.overall_trust_outcome is TrustOutcome.TRUSTWORTHY


def test_false_precision_citation_is_not_trustworthy_even_when_answer_is_correct() -> None:
    repository = _repository()
    evaluator = AnswerLayerEvaluator(repository)

    result = evaluator.evaluate(
        AnswerLayerRunInput(
            case_id="istruct_rn3_006",
            answer_text="The nearest stable parent section.",
            citations=[
                _citation(
                    doc_id="research-notes-3",
                    section_path=["6. Imported Debugging Notes", "Notes"],
                )
            ],
        )
    )

    assert result.support_alignment.verdict is CriterionVerdict.PASS
    assert result.provenance_quality.verdict is CriterionVerdict.FAIL
    assert result.overall_trust_outcome is TrustOutcome.NOT_TRUSTWORTHY
