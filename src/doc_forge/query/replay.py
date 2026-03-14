"""Internal replay primitives for persisted query runs."""

from __future__ import annotations

import structlog
from pydantic import BaseModel, ConfigDict, Field

from doc_forge.app.log_events import LogEvent
from doc_forge.app.logging import get_logger
from doc_forge.identifiers import QueryId

from .contracts import (
    AnswerDraft,
    AnswerMode,
    AnswerModeDecision,
    ContextManifest,
    CorpusSnapshot,
    EvidenceSet,
    FinalQueryArtifacts,
    InterpretedQuery,
    QueryRequest,
    RetrievedCandidate,
    SupportAssessment,
    SupportQualifierReason,
    TrustFailureLabel,
)
from .persistence import QueryAnswerStore, QueryRunStore, QuerySnapshotStore, QueryTraceStore
from .policies import QueryPolicy
from .stages.assess_support import SupportAssessmentTracePayload
from .stages.context import ContextAssemblyTracePayload
from .stages.decide_answer_mode import AnswerModeDecisionTracePayload
from .stages.generate import GenerateTracePayload
from .stages.select import SelectionTracePayload
from .trace import QueryStageTrace, QueryTraceBundle

logger = get_logger(__name__)


class QueryReplayBundle(BaseModel):
    """Frozen persisted artifact bundle used for replay and regression checks."""

    model_config = ConfigDict(extra="forbid")

    query_id: QueryId = Field(min_length=1)
    request: QueryRequest
    policy: QueryPolicy
    snapshot: CorpusSnapshot | None = None
    trace_bundle: QueryTraceBundle
    final_artifacts: FinalQueryArtifacts | None = None


class ReconstructedQueryInputs(BaseModel):
    """Stage-input reconstruction derived from a replay bundle."""

    model_config = ConfigDict(extra="forbid")

    request: QueryRequest
    policy: QueryPolicy
    snapshot: CorpusSnapshot | None = None
    interpreted_query: InterpretedQuery | None = None
    retrieved_candidates: list[RetrievedCandidate] = Field(default_factory=list)
    selected_candidates: list[RetrievedCandidate] = Field(default_factory=list)
    evidence_sets: list[EvidenceSet] = Field(default_factory=list)
    context_manifest: ContextManifest | None = None
    support_assessment: SupportAssessment | None = None
    answer_mode_decision: AnswerModeDecision | None = None
    answer_draft: AnswerDraft | None = None


class QueryReplayLogger:
    def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
        self._logger = logger

    def bundle_built(self, query_id: QueryId, status: str, trace_count: int) -> None:
        self._logger.info(
            LogEvent.REPLAY_BUNDLE_BUILT,
            query_id=query_id,
            status=status,
            trace_count=trace_count,
        )


class QueryReplayService:
    """Read-only replay helper over persisted query artifacts."""

    def __init__(
        self,
        *,
        run_store: QueryRunStore,
        snapshot_store: QuerySnapshotStore,
        trace_store: QueryTraceStore,
        answer_store: QueryAnswerStore,
        logger: QueryReplayLogger | None = None,
    ) -> None:
        self._run_store = run_store
        self._snapshot_store = snapshot_store
        self._trace_store = trace_store
        self._answer_store = answer_store
        self._logger = logger or QueryReplayLogger(get_logger(self.__class__.__name__))

    def build_bundle(self, query_id: QueryId) -> QueryReplayBundle:
        """Load the frozen persisted artifacts required for replay."""

        run = self._run_store.get_query_run(query_id)
        if run is None:
            raise LookupError(f"query run {query_id!r} was not found")
        bundle = QueryReplayBundle(
            query_id=query_id,
            request=QueryRequest(question=run.question, workspace_id=run.workspace_id),
            policy=QueryPolicy.model_validate(run.policy_snapshot),
            snapshot=self._snapshot_store.get_snapshot(query_id),
            trace_bundle=QueryTraceBundle(
                query_id=query_id,
                run_status=run.status,
                stage_traces=self._trace_store.list_stage_traces(query_id),
            ),
            final_artifacts=self._answer_store.get_answer_artifacts(query_id),
        )
        self._logger.bundle_built(
            query_id=query_id,
            status=run.status.value,
            trace_count=len(bundle.trace_bundle.stage_traces),
        )
        return bundle

    def reconstruct_inputs(self, query_id: QueryId) -> ReconstructedQueryInputs:
        """Reconstruct stage inputs from a persisted replay bundle."""

        bundle = self.build_bundle(query_id)
        by_stage = {trace.stage_name.value: trace for trace in bundle.trace_bundle.stage_traces}
        selection_trace = by_stage.get("select")
        context_trace = by_stage.get("assemble_context")
        support_trace = by_stage.get("assess_support")
        answer_mode_trace = by_stage.get("decide_answer_mode")
        generate_trace = by_stage.get("generate")

        interpreted_query = _reconstruct_interpreted_query(by_stage.get("interpret"))
        retrieved_candidates = _reconstruct_retrieved_candidates(by_stage.get("retrieve"))
        selected_candidates, evidence_sets = _reconstruct_selection(selection_trace)
        context_manifest = _reconstruct_context_manifest(context_trace)
        support_assessment = _reconstruct_support_assessment(support_trace)
        answer_mode_decision = _reconstruct_answer_mode_decision(answer_mode_trace)
        answer_draft = _reconstruct_answer_draft(generate_trace)

        return ReconstructedQueryInputs(
            request=bundle.request,
            policy=bundle.policy,
            snapshot=bundle.snapshot,
            interpreted_query=interpreted_query,
            retrieved_candidates=retrieved_candidates,
            selected_candidates=selected_candidates,
            evidence_sets=evidence_sets,
            context_manifest=context_manifest,
            support_assessment=support_assessment,
            answer_mode_decision=answer_mode_decision,
            answer_draft=answer_draft,
        )


def _reconstruct_interpreted_query(trace: QueryStageTrace | None) -> InterpretedQuery | None:
    if trace is None:
        return None
    payload = trace.payload.get("interpreted_query")
    if not isinstance(payload, dict):
        return None
    return InterpretedQuery.model_validate(payload)


def _reconstruct_retrieved_candidates(trace: QueryStageTrace | None) -> list[RetrievedCandidate]:
    if trace is None:
        return []
    payload = trace.payload.get("candidates")
    if not isinstance(payload, list):
        return []
    return [RetrievedCandidate.model_validate(item) for item in payload]


def _reconstruct_selection(
    trace: QueryStageTrace | None,
) -> tuple[list[RetrievedCandidate], list[EvidenceSet]]:
    if trace is None:
        return [], []
    payload = SelectionTracePayload.model_validate(trace.payload)
    return payload.selected_candidates, payload.evidence_sets


def _reconstruct_context_manifest(trace: QueryStageTrace | None) -> ContextManifest | None:
    if trace is None:
        return None
    payload = ContextAssemblyTracePayload.model_validate(trace.payload)
    return ContextManifest(
        ordered_evidence_set_ids=payload.ordered_evidence_set_ids,
        included_evidence_set_ids=payload.included_evidence_set_ids,
        dropped_evidence_set_ids=payload.dropped_evidence_set_ids,
        inclusion_reasons=payload.inclusion_reasons,
        exclusion_reasons=payload.exclusion_reasons,
        token_budget=payload.token_budget,
        token_budget_used=payload.token_budget_used,
        context_items=payload.context_items,
        duplicate_suppression_notes=payload.duplicate_suppression_notes,
    )


def _reconstruct_support_assessment(trace: QueryStageTrace | None) -> SupportAssessment | None:
    if trace is None:
        return None
    payload = SupportAssessmentTracePayload.model_validate(trace.payload)
    return SupportAssessment(
        support_state=payload.final_support_state,
        qualifying_reason_codes=[
            SupportQualifierReason(reason) for reason in payload.qualifying_reason_codes
        ],
        trust_failure_labels=[TrustFailureLabel(label) for label in payload.trust_failure_labels],
        summary=payload.summary,
        unsupported_gaps=payload.unsupported_gaps,
        conflicting_evidence_notes=payload.conflicting_evidence_notes,
        provenance_warnings=payload.provenance_warnings,
    )


def _reconstruct_answer_mode_decision(trace: QueryStageTrace | None) -> AnswerModeDecision | None:
    if trace is None:
        return None
    payload = AnswerModeDecisionTracePayload.model_validate(trace.payload)
    return AnswerModeDecision(
        answer_mode=AnswerMode(payload.final_answer_mode),
        rationale="Reconstructed from persisted answer-mode trace.",
        based_on_support_state=payload.based_on_support_state,
        required_qualifying_reason_codes=payload.qualifying_reason_codes,
        allowed_scope_summary=payload.allowed_scope_summary,
        must_surface_conflict=payload.must_surface_conflict,
    )


def _reconstruct_answer_draft(trace: QueryStageTrace | None) -> AnswerDraft | None:
    if trace is None:
        return None
    payload = GenerateTracePayload.model_validate(trace.payload)
    return AnswerDraft(
        answer_text=payload.answer_text,
        visible_limitations=payload.visible_limitations,
        should_render_citations=payload.should_render_citations,
        grounded_evidence_set_ids=payload.grounded_evidence_set_ids,
        generator_version=payload.generator_version,
    )
