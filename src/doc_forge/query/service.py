"""Internal query orchestration seam for Stage 0 scaffolding."""

from __future__ import annotations

import hashlib
import typing
from datetime import datetime
from uuid import uuid4

import structlog
from structlog.contextvars import bind_contextvars, unbind_contextvars

from doc_forge.app.log_events import LogEvent
from doc_forge.app.logging import get_logger
from doc_forge.readmodels import QueryableCorpusReadModel

from .answer_generation import DeterministicGroundedAnswerGenerator, GroundedAnswerGenerator
from .answer_mode_policy import AnswerModePolicy
from .citation_rendering import CitationRenderer, DeterministicCitationRenderer
from .context_assembly import ContextAssembler
from .contracts import (
    CorpusSnapshot,
    FinalQueryArtifacts,
    QueryRequest,
    QueryRun,
    QueryRunStatus,
    QueryStageName,
    QueryTerminalFailure,
    TrustFailureLabel,
)
from .domain import QueryRuntimeState
from .errors import (
    CorpusBoundaryUnavailableError,
    QueryExecutionFailedError,
    QueryStageContractViolationError,
    QueryStageNotImplementedError,
)
from .interpretation import DeterministicQueryInterpreter, QueryInterpreter
from .persistence import QueryAnswerStore, QueryRunStore, QuerySnapshotStore, QueryTraceStore
from .policies import QueryPolicy, QueryPolicyDefaults, apply_policy_overrides
from .retrieval import DenseQueryRetriever
from .selection import QuerySelector
from .stages.assess_support import run as run_assess_support_stage
from .stages.context import run as run_context_stage
from .stages.decide_answer_mode import run as run_decide_answer_mode_stage
from .stages.generate import run as run_generate_stage
from .stages.interpret import run as run_interpret_stage
from .stages.render_citations import run as run_render_citations_stage
from .stages.retrieve import run as run_retrieve_stage
from .stages.select import run as run_select_stage
from .support_assessment import HybridSupportAssessor
from .trace import QueryStageTrace, utc_now

logger = get_logger(__name__)


class QueryServiceLogger:
    def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
        self._logger = logger

    def run_started(
        self, status: str, question_chars: int, question_sha256: str, snapshot_doc_count: int
    ) -> None:
        self._logger.info(
            LogEvent.QUERY_RUN_STARTED,
            status=status,
            question_chars=question_chars,
            question_sha256=question_sha256,
            snapshot_doc_count=snapshot_doc_count,
        )

    def stage_started(self, stage_name: str) -> None:
        self._logger.info(LogEvent.QUERY_STAGE_STARTED, stage_name=stage_name)

    def run_completed(
        self, status: str, support_state: str, answer_mode: str, citation_count: int
    ) -> None:
        self._logger.info(
            LogEvent.QUERY_RUN_COMPLETED,
            status=status,
            support_state=support_state,
            answer_mode=answer_mode,
            citation_count=citation_count,
        )

    def run_failed(
        self,
        stage_name: str | None,
        error_code: str,
        error_class: str,
        message: str,
        trust_failure_labels: list[str] | None = None,
    ) -> None:
        self._logger.exception(
            LogEvent.QUERY_RUN_FAILED,
            stage_name=stage_name,
            error_code=error_code,
            error_class=error_class,
            message=message,
            trust_failure_labels=trust_failure_labels,
        )

    def stage_completed(
        self, stage_name: str, status: str, duration_ms: int | None, **extra: typing.Any
    ) -> None:
        self._logger.info(
            LogEvent.QUERY_STAGE_COMPLETED,
            stage_name=stage_name,
            status=status,
            duration_ms=duration_ms,
            **extra,
        )


class QueryService:
    """Prepare query runtime state without pretending execution exists yet."""

    def __init__(
        self,
        *,
        base_policy: QueryPolicy | None = None,
        corpus_read_model: QueryableCorpusReadModel | None = None,
        run_store: QueryRunStore | None = None,
        snapshot_store: QuerySnapshotStore | None = None,
        trace_store: QueryTraceStore | None = None,
        interpreter: QueryInterpreter | None = None,
        retriever: DenseQueryRetriever | None = None,
        selector: QuerySelector | None = None,
        context_assembler: ContextAssembler | None = None,
        support_assessor: HybridSupportAssessor | None = None,
        answer_mode_policy: AnswerModePolicy | None = None,
        answer_generator: GroundedAnswerGenerator | None = None,
        citation_renderer: CitationRenderer | None = None,
        answer_store: QueryAnswerStore | None = None,
        logger: QueryServiceLogger | None = None,
    ) -> None:
        self._base_policy = base_policy or QueryPolicyDefaults.build()
        self._corpus_read_model = corpus_read_model
        self._run_store = run_store
        self._snapshot_store = snapshot_store
        self._trace_store = trace_store
        self._interpreter = interpreter or DeterministicQueryInterpreter()
        self._retriever = retriever
        self._selector = selector
        self._context_assembler = context_assembler
        self._support_assessor = support_assessor
        self._answer_mode_policy = answer_mode_policy
        self._answer_generator = answer_generator or DeterministicGroundedAnswerGenerator()
        self._citation_renderer = citation_renderer or DeterministicCitationRenderer()
        self._answer_store = answer_store
        self._logger = logger or QueryServiceLogger(get_logger(self.__class__.__name__))

    @property
    def base_policy(self) -> QueryPolicy:
        """Return the canonical base query policy."""

        return self._base_policy

    @property
    def trace_store(self) -> QueryTraceStore | None:
        """Expose the optional trace store for future stage wiring."""

        return self._trace_store

    @property
    def snapshot_store(self) -> QuerySnapshotStore | None:
        """Expose the optional snapshot store for query-boundary persistence."""

        return self._snapshot_store

    def resolve_policy(self, request: QueryRequest) -> QueryPolicy:
        """Resolve the effective policy for a request."""

        return apply_policy_overrides(self._base_policy, request.policy_overrides)

    def create_run(self, request: QueryRequest) -> QueryRun:
        """Create and optionally persist a Stage 0 query run envelope."""

        policy = self.resolve_policy(request)
        run = QueryRun(
            query_id=f"qry-{uuid4().hex}",
            workspace_id=request.workspace_id,
            question=request.question,
            status=QueryRunStatus.PENDING,
            policy_snapshot=policy.model_dump(mode="json"),
        )
        if self._run_store is not None:
            return self._run_store.create_query_run(run)
        return run

    def initialize_runtime_state(self, request: QueryRequest) -> QueryRuntimeState:
        """Initialize query runtime state without executing any stages."""

        return QueryRuntimeState(
            request=request,
            run=self.create_run(request),
        )

    def capture_snapshot(
        self,
        request: QueryRequest,
        *,
        query_started_at: datetime | None = None,
    ) -> CorpusSnapshot:
        """Capture the stable corpus snapshot for a query request."""

        if self._corpus_read_model is None:
            raise CorpusBoundaryUnavailableError("query corpus read model is not configured")
        return self._corpus_read_model.capture_snapshot(
            request.workspace_id,
            query_started_at=query_started_at,
        )

    def prepare_query(self, request: QueryRequest) -> QueryRuntimeState:
        """Create a query run and capture its stable corpus snapshot."""

        run = self.create_run(request)
        snapshot = self.capture_snapshot(request, query_started_at=run.submitted_at)
        if self._snapshot_store is not None:
            self._snapshot_store.save_snapshot(run.query_id, snapshot)
        return QueryRuntimeState(
            request=request,
            run=run,
            snapshot=snapshot,
        )

    def execute_until_interpretation(self, request: QueryRequest) -> QueryRuntimeState:
        """Run the query lifecycle through the Stage-2 interpretation stage."""

        state = self.prepare_query(request)
        state.run.status = QueryRunStatus.RUNNING
        if self._run_store is not None:
            state.run = self._run_store.update_query_run_status(
                state.run.query_id,
                QueryRunStatus.RUNNING,
            )
        if state.snapshot is None:
            raise CorpusBoundaryUnavailableError("query corpus snapshot was not captured")
        result = run_interpret_stage(
            query_id=state.run.query_id,
            request=request,
            snapshot=state.snapshot,
            interpreter=self._interpreter,
        )
        state.interpreted_query = result.interpretation.interpreted_query
        if self._trace_store is not None:
            self._trace_store.append_stage_trace(result.trace)
        return state

    def execute_until_retrieval(self, request: QueryRequest) -> QueryRuntimeState:
        """Run the query lifecycle through the Stage-3 retrieval stage."""

        if self._retriever is None:
            raise QueryStageNotImplementedError("retrieve stage is not configured")
        state = self.execute_until_interpretation(request)
        if state.snapshot is None:
            raise CorpusBoundaryUnavailableError("query corpus snapshot was not captured")
        if state.interpreted_query is None:
            raise QueryStageNotImplementedError(
                "interpret stage did not produce an interpreted query"
            )
        result = run_retrieve_stage(
            query_id=state.run.query_id,
            request=request,
            snapshot=state.snapshot,
            interpreted_query=state.interpreted_query,
            policy=self.resolve_policy(request),
            retriever=self._retriever,
        )
        state.retrieved_candidates = result.retrieval.candidates
        if self._trace_store is not None:
            self._trace_store.append_stage_trace(result.trace)
        return state

    def execute_until_selection(self, request: QueryRequest) -> QueryRuntimeState:
        """Run the query lifecycle through the Stage-4 selection stage."""

        if self._selector is None:
            raise QueryStageNotImplementedError("select stage is not configured")
        state = self.execute_until_retrieval(request)
        if state.snapshot is None:
            raise CorpusBoundaryUnavailableError("query corpus snapshot was not captured")
        if state.interpreted_query is None:
            raise QueryStageNotImplementedError(
                "interpret stage did not produce an interpreted query"
            )
        result = run_select_stage(
            query_id=state.run.query_id,
            request=request,
            snapshot=state.snapshot,
            interpreted_query=state.interpreted_query,
            retrieved_candidates=state.retrieved_candidates,
            policy=self.resolve_policy(request),
            selector=self._selector,
        )
        state.selected_candidates = result.selection.selected_candidates
        state.evidence_sets = result.selection.evidence_sets
        if self._trace_store is not None:
            self._trace_store.append_stage_trace(result.trace)
        return state

    def execute(self, request: QueryRequest) -> QueryRuntimeState:
        """Execute the deepest configured query lifecycle path."""

        if self._corpus_read_model is None:
            raise QueryStageNotImplementedError("query corpus read model is not configured")
        if self._answer_store is not None:
            return self.execute_until_answer(request)
        if self._support_assessor is not None and self._answer_mode_policy is not None:
            state = self.execute_until_answer_mode(request)
        elif self._context_assembler is not None:
            state = self.execute_until_context_assembly(request)
        elif self._selector is not None:
            state = self.execute_until_selection(request)
        elif self._retriever is not None:
            state = self.execute_until_retrieval(request)
        else:
            state = self.execute_until_interpretation(request)
        raise QueryStageNotImplementedError(
            "Query execution is not implemented beyond the deepest configured stage for "
            f"{state.run.query_id}",
        )

    def execute_until_context_assembly(self, request: QueryRequest) -> QueryRuntimeState:
        """Run the query lifecycle through the Stage-5 context-assembly stage."""

        if self._context_assembler is None:
            raise QueryStageNotImplementedError("assemble_context stage is not configured")
        state = self.execute_until_selection(request)
        if state.snapshot is None:
            raise CorpusBoundaryUnavailableError("query corpus snapshot was not captured")
        if state.interpreted_query is None:
            raise QueryStageNotImplementedError(
                "interpret stage did not produce an interpreted query"
            )
        result = run_context_stage(
            query_id=state.run.query_id,
            request=request,
            snapshot=state.snapshot,
            interpreted_query=state.interpreted_query,
            evidence_sets=state.evidence_sets,
            policy=self.resolve_policy(request),
            assembler=self._context_assembler,
        )
        state.context_manifest = result.context_assembly.manifest
        if self._trace_store is not None:
            self._trace_store.append_stage_trace(result.trace)
        return state

    def execute_until_answer_mode(self, request: QueryRequest) -> QueryRuntimeState:
        """Run the query lifecycle through the Stage-6 answer-mode stage."""

        if self._support_assessor is None:
            raise QueryStageNotImplementedError("assess_support stage is not configured")
        if self._answer_mode_policy is None:
            raise QueryStageNotImplementedError("decide_answer_mode stage is not configured")
        state = self.execute_until_context_assembly(request)
        if state.snapshot is None:
            raise CorpusBoundaryUnavailableError("query corpus snapshot was not captured")
        if state.interpreted_query is None:
            raise QueryStageNotImplementedError(
                "interpret stage did not produce an interpreted query"
            )
        if state.context_manifest is None:
            raise QueryStageNotImplementedError(
                "assemble_context stage did not produce a context manifest"
            )
        support_result = run_assess_support_stage(
            query_id=state.run.query_id,
            request=request,
            snapshot=state.snapshot,
            interpreted_query=state.interpreted_query,
            evidence_sets=state.evidence_sets,
            context_manifest=state.context_manifest,
            policy=self.resolve_policy(request),
            assessor=self._support_assessor,
        )
        state.support_assessment = support_result.support_assessment.assessment
        if self._trace_store is not None:
            self._trace_store.append_stage_trace(support_result.trace)
        answer_mode_result = run_decide_answer_mode_stage(
            query_id=state.run.query_id,
            request=request,
            snapshot=state.snapshot,
            interpreted_query=state.interpreted_query,
            support_assessment=state.support_assessment,
            policy=self.resolve_policy(request),
            answer_mode_policy=self._answer_mode_policy,
        )
        state.answer_mode_decision = answer_mode_result.answer_mode_policy.decision
        if self._trace_store is not None:
            self._trace_store.append_stage_trace(answer_mode_result.trace)
        return state

    def execute_until_answer(self, request: QueryRequest) -> QueryRuntimeState:
        """Run the query lifecycle through Stage 7 final answer completion."""

        if self._answer_store is None:
            raise QueryStageNotImplementedError("final answer persistence is not configured")
        if self._retriever is None:
            raise QueryStageNotImplementedError("retrieve stage is not configured")
        if self._selector is None:
            raise QueryStageNotImplementedError("select stage is not configured")
        if self._context_assembler is None:
            raise QueryStageNotImplementedError("assemble_context stage is not configured")
        if self._support_assessor is None:
            raise QueryStageNotImplementedError("assess_support stage is not configured")
        if self._answer_mode_policy is None:
            raise QueryStageNotImplementedError("decide_answer_mode stage is not configured")
        if self._answer_generator is None:
            raise QueryStageNotImplementedError("generate stage is not configured")
        if self._citation_renderer is None:
            raise QueryStageNotImplementedError("render_citations stage is not configured")
        retriever = self._retriever
        selector = self._selector
        context_assembler = self._context_assembler
        support_assessor = self._support_assessor
        answer_mode_policy = self._answer_mode_policy
        answer_generator = self._answer_generator
        citation_renderer = self._citation_renderer

        state = self.prepare_query(request)
        state.run.status = QueryRunStatus.RUNNING
        if self._run_store is not None:
            state.run = self._run_store.update_query_run_status(
                state.run.query_id,
                QueryRunStatus.RUNNING,
            )
        if state.snapshot is None:
            raise CorpusBoundaryUnavailableError("query corpus snapshot was not captured")

        policy = self.resolve_policy(request)
        current_stage: QueryStageName | None = None
        bind_contextvars(
            query_id=state.run.query_id,
            workspace_id=state.run.workspace_id,
        )
        self._logger.run_started(
            status=state.run.status.value,
            question_chars=len(request.question),
            question_sha256=hashlib.sha256(request.question.encode("utf-8")).hexdigest(),
            snapshot_doc_count=len(state.snapshot.eligible_doc_ids),
        )
        try:
            current_stage = QueryStageName.INTERPRET
            self._logger.stage_started(stage_name=current_stage.value)
            interpret_result = run_interpret_stage(
                query_id=state.run.query_id,
                request=request,
                snapshot=state.snapshot,
                interpreter=self._interpreter,
            )
            state.interpreted_query = interpret_result.interpretation.interpreted_query
            self._append_trace(interpret_result.trace)
            self._log_stage_completed(interpret_result.trace)

            current_stage = QueryStageName.RETRIEVE
            self._logger.stage_started(stage_name=current_stage.value)
            retrieve_result = run_retrieve_stage(
                query_id=state.run.query_id,
                request=request,
                snapshot=state.snapshot,
                interpreted_query=state.interpreted_query,
                policy=policy,
                retriever=retriever,
            )
            state.retrieved_candidates = retrieve_result.retrieval.candidates
            self._append_trace(retrieve_result.trace)
            self._log_stage_completed(
                retrieve_result.trace,
                candidate_count=len(state.retrieved_candidates),
            )

            current_stage = QueryStageName.SELECT
            self._logger.stage_started(stage_name=current_stage.value)
            select_result = run_select_stage(
                query_id=state.run.query_id,
                request=request,
                snapshot=state.snapshot,
                interpreted_query=state.interpreted_query,
                retrieved_candidates=state.retrieved_candidates,
                policy=policy,
                selector=selector,
            )
            state.selected_candidates = select_result.selection.selected_candidates
            state.evidence_sets = select_result.selection.evidence_sets
            self._append_trace(select_result.trace)
            self._log_stage_completed(
                select_result.trace,
                selected_candidate_count=len(state.selected_candidates),
                evidence_set_count=len(state.evidence_sets),
            )

            current_stage = QueryStageName.ASSEMBLE_CONTEXT
            self._logger.stage_started(stage_name=current_stage.value)
            context_result = run_context_stage(
                query_id=state.run.query_id,
                request=request,
                snapshot=state.snapshot,
                interpreted_query=state.interpreted_query,
                evidence_sets=state.evidence_sets,
                policy=policy,
                assembler=context_assembler,
            )
            state.context_manifest = context_result.context_assembly.manifest
            self._append_trace(context_result.trace)
            self._log_stage_completed(
                context_result.trace,
                included_evidence_set_count=len(state.context_manifest.included_evidence_set_ids),
                context_item_count=len(state.context_manifest.context_items),
            )

            current_stage = QueryStageName.ASSESS_SUPPORT
            self._logger.stage_started(stage_name=current_stage.value)
            support_result = run_assess_support_stage(
                query_id=state.run.query_id,
                request=request,
                snapshot=state.snapshot,
                interpreted_query=state.interpreted_query,
                evidence_sets=state.evidence_sets,
                context_manifest=state.context_manifest,
                policy=policy,
                assessor=support_assessor,
            )
            state.support_assessment = support_result.support_assessment.assessment
            self._append_trace(support_result.trace)
            self._log_stage_completed(
                support_result.trace,
                support_state=state.support_assessment.support_state.value,
                qualifying_reason_codes=[
                    reason.value for reason in state.support_assessment.qualifying_reason_codes
                ],
            )

            current_stage = QueryStageName.DECIDE_ANSWER_MODE
            self._logger.stage_started(stage_name=current_stage.value)
            answer_mode_result = run_decide_answer_mode_stage(
                query_id=state.run.query_id,
                request=request,
                snapshot=state.snapshot,
                interpreted_query=state.interpreted_query,
                support_assessment=state.support_assessment,
                policy=policy,
                answer_mode_policy=answer_mode_policy,
            )
            state.answer_mode_decision = answer_mode_result.answer_mode_policy.decision
            self._append_trace(answer_mode_result.trace)
            self._log_stage_completed(
                answer_mode_result.trace,
                answer_mode=state.answer_mode_decision.answer_mode.value,
            )

            current_stage = QueryStageName.GENERATE
            self._logger.stage_started(stage_name=current_stage.value)
            generate_result = run_generate_stage(
                query_id=state.run.query_id,
                request=request,
                snapshot=state.snapshot,
                interpreted_query=state.interpreted_query,
                context_manifest=state.context_manifest,
                support_assessment=state.support_assessment,
                answer_mode_decision=state.answer_mode_decision,
                policy=policy,
                generator=answer_generator,
            )
            state.answer_draft = generate_result.generation.answer_draft
            self._append_trace(generate_result.trace)
            self._log_stage_completed(
                generate_result.trace,
                answer_chars=len(state.answer_draft.answer_text),
                grounded_evidence_set_count=len(state.answer_draft.grounded_evidence_set_ids),
            )

            current_stage = QueryStageName.RENDER_CITATIONS
            self._logger.stage_started(stage_name=current_stage.value)
            render_result = run_render_citations_stage(
                query_id=state.run.query_id,
                request=request,
                snapshot=state.snapshot,
                interpreted_query=state.interpreted_query,
                evidence_sets=state.evidence_sets,
                context_manifest=state.context_manifest,
                support_assessment=state.support_assessment,
                answer_mode_decision=state.answer_mode_decision,
                answer_draft=state.answer_draft,
                policy=policy,
                renderer=citation_renderer,
            )
            state.citation_bundle = render_result.rendering.citation_bundle
            self._append_trace(render_result.trace)
            self._log_stage_completed(
                render_result.trace,
                citation_count=len(state.citation_bundle.citations),
                citation_doc_count=len(state.citation_bundle.material_doc_ids),
            )

            if state.answer_draft.should_render_citations and not state.citation_bundle.citations:
                raise QueryStageContractViolationError(
                    "non-abstaining answers must not complete without citations"
                )

            self._answer_store.save_answer_artifacts(
                state.run.query_id,
                FinalQueryArtifacts(
                    answer=state.answer_draft,
                    citations=state.citation_bundle,
                    support_state=state.support_assessment.support_state,
                    qualifying_reason_codes=state.support_assessment.qualifying_reason_codes,
                    answer_mode=state.answer_mode_decision.answer_mode,
                    trust_failure_labels=state.support_assessment.trust_failure_labels,
                ),
            )
            completed_at = utc_now()
            if self._run_store is not None:
                state.run = self._run_store.update_query_run_status(
                    state.run.query_id,
                    QueryRunStatus.SUCCEEDED,
                    completed_at=completed_at,
                )
            else:
                state.run.status = QueryRunStatus.SUCCEEDED
                state.run.completed_at = completed_at
            self._logger.run_completed(
                status=state.run.status.value,
                support_state=state.support_assessment.support_state.value,
                answer_mode=state.answer_mode_decision.answer_mode.value,
                citation_count=len(state.citation_bundle.citations),
            )
            return state
        except Exception as exc:
            terminal_failure = _build_terminal_failure(exc, current_stage)
            completed_at = utc_now()
            if self._run_store is not None:
                state.run = self._run_store.update_query_run_status(
                    state.run.query_id,
                    QueryRunStatus.FAILED,
                    completed_at=completed_at,
                    terminal_failure=terminal_failure,
                )
            else:
                state.run.status = QueryRunStatus.FAILED
                state.run.completed_at = completed_at
                state.run.terminal_failure = terminal_failure
            self._logger.run_failed(
                stage_name=None if current_stage is None else current_stage.value,
                error_code=terminal_failure.error_code,
                error_class=terminal_failure.error_class,
                message=terminal_failure.message,
                trust_failure_labels=[
                    label.value for label in terminal_failure.trust_failure_labels
                ],
            )
            raise QueryExecutionFailedError(
                query_id=state.run.query_id,
                terminal_failure=terminal_failure,
            ) from exc
        finally:
            unbind_contextvars("query_id", "workspace_id")

    def _append_trace(self, trace: QueryStageTrace) -> None:
        if self._trace_store is not None:
            self._trace_store.append_stage_trace(trace)

    def _log_stage_completed(self, trace: QueryStageTrace, **extra: object) -> None:
        self._logger.stage_completed(
            stage_name=trace.stage_name.value,
            status=trace.stage_status.value,
            duration_ms=_duration_ms(trace),
            **extra,
        )


def _duration_ms(trace: QueryStageTrace) -> int | None:
    if trace.finished_at is None:
        return None
    return max(int((trace.finished_at - trace.started_at).total_seconds() * 1000), 0)


def _build_terminal_failure(
    exc: Exception,
    stage_name: QueryStageName | None,
) -> QueryTerminalFailure:
    trust_failure_labels: list[TrustFailureLabel] = []
    if isinstance(exc, QueryStageContractViolationError):
        if stage_name is QueryStageName.RENDER_CITATIONS:
            trust_failure_labels.append(TrustFailureLabel.P1)
        error_code = "query_stage_contract_violation"
    elif isinstance(exc, CorpusBoundaryUnavailableError):
        error_code = "corpus_boundary_unavailable"
    elif isinstance(exc, QueryStageNotImplementedError):
        error_code = "query_stage_not_implemented"
    else:
        error_code = "query_execution_failed"
    return QueryTerminalFailure(
        error_code=error_code,
        error_class=exc.__class__.__name__,
        stage_name=stage_name,
        message=_truncate_message(str(exc)),
        trust_failure_labels=trust_failure_labels,
    )


def _truncate_message(message: str, *, limit: int = 240) -> str:
    if len(message) <= limit:
        return message
    return f"{message[: limit - 3]}..."
