from __future__ import annotations

from doc_forge.query import (
    CorpusSnapshot,
    QueryRequest,
    QueryRequestType,
    QuerySpecificity,
    SynthesisMode,
    UnsupportedCapability,
)
from doc_forge.query.interpretation import DeterministicQueryInterpreter


def _interpret(question: str):
    interpreter = DeterministicQueryInterpreter()
    result = interpreter.interpret(
        request=QueryRequest(question=question, workspace_id="ws-1"),
        snapshot=CorpusSnapshot(workspace_id="ws-1", eligible_doc_ids=[]),
    )
    return result.interpreted_query


def test_deterministic_interpreter_classifies_explanation_requests() -> None:
    interpreted = _interpret(" Explain the retry strategy in chapter 2. ")

    assert interpreted.request_type is QueryRequestType.EXPLANATION
    assert interpreted.answer_shape == "section_scoped_explanation"
    assert interpreted.specificity is QuerySpecificity.SECTION_SCOPED
    assert interpreted.normalization_notes == [
        "lowercased",
        "trimmed_terminal_punctuation",
        "trimmed_whitespace",
    ]


def test_deterministic_interpreter_marks_cross_document_synthesis() -> None:
    interpreted = _interpret("What do these documents say about caching?")

    assert interpreted.request_type is QueryRequestType.SYNTHESIS
    assert interpreted.requires_synthesis is True
    assert interpreted.synthesis_mode is SynthesisMode.CROSS_DOCUMENT
    assert interpreted.answer_shape == "multi_source_synthesis"


def test_deterministic_interpreter_marks_source_navigation_requests() -> None:
    interpreted = _interpret("Which section explains retries?")

    assert interpreted.request_type is QueryRequestType.SOURCE_NAVIGATION
    assert interpreted.requires_source_navigation is True
    assert interpreted.answer_shape == "source_location"


def test_deterministic_interpreter_surfaces_unsupported_capabilities() -> None:
    interpreted = _interpret("What does the figure on page 3 show?")

    assert interpreted.request_type is QueryRequestType.UNSUPPORTED
    assert interpreted.answer_shape == "capability_boundary_response"
    assert [flag.value for flag in interpreted.unsupported_capability_flags] == [
        "image_or_figure_reasoning"
    ]


def test_deterministic_interpreter_marks_heatmap_value_questions_as_unsupported() -> None:
    interpreted = _interpret(
        "What exact cell value does the latency heatmap show for the top-4 setting?"
    )

    assert interpreted.request_type is QueryRequestType.UNSUPPORTED
    assert interpreted.answer_shape == "capability_boundary_response"
    assert interpreted.unsupported_capability_flags == [
        UnsupportedCapability.IMAGE_OR_FIGURE_REASONING
    ]


def test_deterministic_interpreter_normalizes_equivalent_requests_consistently() -> None:
    first = _interpret("What is semantic retrieval?")
    second = _interpret("  what is   semantic retrieval?! ")

    first_payload = first.model_dump()
    second_payload = second.model_dump()
    del first_payload["normalization_notes"]
    del second_payload["normalization_notes"]

    assert first_payload == second_payload
