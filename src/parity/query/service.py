"""Internal query orchestration seam for Stage 0 scaffolding."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from parity.readmodels import QueryableCorpusReadModel

from .contracts import CorpusSnapshot, QueryRequest, QueryRun, QueryRunStatus
from .domain import QueryRuntimeState
from .errors import CorpusBoundaryUnavailableError
from .errors import QueryStageNotImplementedError
from .persistence import QueryRunStore, QuerySnapshotStore, QueryTraceStore
from .policies import QueryPolicy, QueryPolicyDefaults, apply_policy_overrides


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
    ) -> None:
        self._base_policy = base_policy or QueryPolicyDefaults.build()
        self._corpus_read_model = corpus_read_model
        self._run_store = run_store
        self._snapshot_store = snapshot_store
        self._trace_store = trace_store

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

    def execute(self, request: QueryRequest) -> QueryRuntimeState:
        """Reject execution until later stages are implemented."""

        if self._corpus_read_model is None:
            state = self.initialize_runtime_state(request)
        else:
            state = self.prepare_query(request)
        raise QueryStageNotImplementedError(
            f"Query execution is not implemented in Stage 0 scaffolding for {state.run.query_id}",
        )
