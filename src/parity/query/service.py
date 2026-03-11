"""Internal query orchestration seam for Stage 0 scaffolding."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from parity.readmodels import QueryableCorpusReadModel

from .context_assembly import ContextAssembler
from .contracts import CorpusSnapshot, QueryRequest, QueryRun, QueryRunStatus
from .domain import QueryRuntimeState
from .errors import CorpusBoundaryUnavailableError, QueryStageNotImplementedError
from .interpretation import DeterministicQueryInterpreter, QueryInterpreter
from .persistence import QueryRunStore, QuerySnapshotStore, QueryTraceStore
from .policies import QueryPolicy, QueryPolicyDefaults, apply_policy_overrides
from .retrieval import DenseQueryRetriever
from .selection import QuerySelector
from .stages.context import run as run_context_stage
from .stages.interpret import run as run_interpret_stage
from .stages.retrieve import run as run_retrieve_stage
from .stages.select import run as run_select_stage


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
        """Reject execution until later stages are implemented."""

        if self._corpus_read_model is None:
            state = self.initialize_runtime_state(request)
        elif self._context_assembler is not None:
            state = self.execute_until_context_assembly(request)
        elif self._selector is not None:
            state = self.execute_until_selection(request)
        elif self._retriever is not None:
            state = self.execute_until_retrieval(request)
        else:
            state = self.execute_until_interpretation(request)
        raise QueryStageNotImplementedError(
            f"Query execution is not implemented beyond context assembly for {state.run.query_id}",
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
