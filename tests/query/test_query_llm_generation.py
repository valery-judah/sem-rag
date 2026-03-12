from __future__ import annotations

from parity.query.answer_generation import MlxGroundedAnswerGenerator, OllamaGroundedAnswerGenerator
from parity.query.contracts import (
    AnswerMode,
    AnswerModeDecision,
    ContextItem,
    ContextManifest,
    CorpusSnapshot,
    InterpretedQuery,
    QueryRequest,
    QueryRequestType,
    QuerySpecificity,
    SupportAssessment,
    SupportState,
    SynthesisMode,
)
from parity.query.policies import QueryPolicyDefaults


class _FakeLlmBackend:
    def __init__(self, answer_text: str) -> None:
        self.answer_text = answer_text
        self.calls: list[dict[str, object]] = []

    def generate(
        self,
        *,
        model_name: str,
        prompt: str,
        max_new_tokens: int,
        temperature: float,
    ) -> str:
        self.calls.append(
            {
                "model_name": model_name,
                "prompt": prompt,
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
            }
        )
        return self.answer_text


def _interpreted_query(**overrides: object) -> InterpretedQuery:
    return InterpretedQuery(
        normalized_question="what uses embeddings to retrieve related passages",
        request_type=QueryRequestType.FACT_LOOKUP,
        answer_shape="direct answer",
        specificity=QuerySpecificity.PRECISE,
        requires_synthesis=False,
        synthesis_mode=SynthesisMode.NONE,
        requires_source_navigation=False,
        unsupported_capability_flags=[],
        normalization_notes=[],
    ).model_copy(update=overrides)


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


def test_mlx_grounded_answer_generator_uses_backend_for_supported_answers() -> None:
    backend = _FakeLlmBackend("A local model can answer from the grounded evidence.")
    generator = MlxGroundedAnswerGenerator(
        model_name="mlx-community/test-model",
        max_new_tokens=128,
        temperature=0.1,
        backend=backend,
    )

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

    assert result.answer_draft.answer_text == "A local model can answer from the grounded evidence."
    assert result.answer_draft.grounded_evidence_set_ids == ["es-1"]
    assert result.answer_draft.should_render_citations is True
    assert result.generator_version == "answer_generation.mlx.v1"
    assert len(backend.calls) == 1
    assert backend.calls[0]["model_name"] == "mlx-community/test-model"
    assert "Grounded context" in str(backend.calls[0]["prompt"])
    assert "What uses embeddings to retrieve related passages?" in str(backend.calls[0]["prompt"])


def test_mlx_grounded_answer_generator_falls_back_for_full_abstention() -> None:
    backend = _FakeLlmBackend("This should not be used.")
    generator = MlxGroundedAnswerGenerator(backend=backend)

    result = generator.generate(
        request=QueryRequest(question="What is available in the corpus?", workspace_id="ws-1"),
        snapshot=CorpusSnapshot(workspace_id="ws-1", eligible_doc_ids=[]),
        interpreted_query=_interpreted_query(),
        context_manifest=_context_manifest(evidence_set_ids=[]),
        support_assessment=SupportAssessment(support_state=SupportState.INSUFFICIENT),
        answer_mode_decision=AnswerModeDecision(
            answer_mode=AnswerMode.FULL_ABSTENTION,
            rationale="Insufficient support requires abstention.",
            based_on_support_state=SupportState.INSUFFICIENT,
        ),
        policy=QueryPolicyDefaults.build(),
    )

    assert "does not provide enough support" in result.answer_draft.answer_text
    assert result.answer_draft.should_render_citations is False
    assert backend.calls == []


def test_ollama_grounded_answer_generator_uses_grounded_prompt_for_supported_answers() -> None:
    backend = _FakeLlmBackend("Atlas has stricter freshness guarantees.")
    generator = OllamaGroundedAnswerGenerator(
        model_name="tinyllama",
        max_new_tokens=128,
        temperature=0.0,
        backend=backend,
    )

    result = generator.generate(
        request=QueryRequest(
            question="Compare Atlas and Beacon caching strategies.",
            workspace_id="ws-1",
        ),
        snapshot=CorpusSnapshot(workspace_id="ws-1", eligible_doc_ids=["doc-1", "doc-2"]),
        interpreted_query=_interpreted_query(),
        context_manifest=_context_manifest(evidence_set_ids=["es-1", "es-2"]),
        support_assessment=SupportAssessment(support_state=SupportState.SUFFICIENT),
        answer_mode_decision=AnswerModeDecision(
            answer_mode=AnswerMode.DIRECT_ANSWER,
            rationale="Sufficient support allows a direct answer.",
            based_on_support_state=SupportState.SUFFICIENT,
        ),
        policy=QueryPolicyDefaults.build(),
    )

    assert result.answer_draft.answer_text == "Atlas has stricter freshness guarantees."
    assert result.generator_version == "answer_generation.ollama.v1"
    assert len(backend.calls) == 1
    assert "Grounded context" in str(backend.calls[0]["prompt"])
    assert "Compare Atlas and Beacon caching strategies." in str(backend.calls[0]["prompt"])


def test_ollama_grounded_answer_generator_discards_prompt_echo_and_falls_back() -> None:
    backend = _FakeLlmBackend(
        "Question: Compare Atlas and Beacon caching strategies.\n\n"
        "Answer: Atlas has stricter freshness guarantees.\n\n"
        "Visible limitations: None\n\n"
        "Grounded context:\nAtlas Cache Design ..."
    )
    generator = OllamaGroundedAnswerGenerator(
        model_name="tinyllama",
        max_new_tokens=128,
        temperature=0.0,
        backend=backend,
    )

    result = generator.generate(
        request=QueryRequest(
            question="Compare Atlas and Beacon caching strategies.",
            workspace_id="ws-1",
        ),
        snapshot=CorpusSnapshot(workspace_id="ws-1", eligible_doc_ids=["doc-1", "doc-2"]),
        interpreted_query=_interpreted_query(
            request_type=QueryRequestType.COMPARISON,
            answer_shape="qualified_comparison",
            specificity=QuerySpecificity.BROAD,
            requires_synthesis=True,
            synthesis_mode=SynthesisMode.CROSS_DOCUMENT,
        ),
        context_manifest=ContextManifest(
            ordered_evidence_set_ids=["es-1"],
            included_evidence_set_ids=["es-1"],
            inclusion_reasons={"es-1": "included_within_budget"},
            token_budget=4000,
            token_budget_used=32,
            context_items=[
                ContextItem(
                    evidence_set_id="es-1",
                    assembly_rank=1,
                    rendered_text=(
                        "Atlas Cache Design | cross_document_synthesis | Atlas > Caching\n"
                        "[p. 2] Atlas Cache Design: Atlas uses immediate invalidation.\n"
                        "[p. 4] Beacon Dashboard Cache: Beacon uses a 15-minute TTL and allows stale reads."
                    ),
                    contributing_doc_ids=["doc-1", "doc-2"],
                    heading_paths=[["Atlas", "Caching"], ["Beacon", "Caching"]],
                    locators=["p. 2", "p. 4"],
                    estimated_token_count=16,
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

    assert "Grounded context" not in result.answer_draft.answer_text
    assert "Question:" not in result.answer_draft.answer_text
    assert "Atlas Cache Design has stricter freshness guarantees" in result.answer_draft.answer_text
