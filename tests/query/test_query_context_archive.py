from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from doc_forge.corpus import SourceReference
from doc_forge.query import (
    AnswerDraft,
    AnswerMode,
    CitationBundle,
    CitationRecord,
    CitationSupportRole,
    CollectedQueryContext,
    FinalQueryArtifacts,
    QueryContextCollectionExtras,
    QueryContextCollector,
    QueryContextManifest,
    QueryContextSourceKind,
    QueryPolicyDefaults,
    QueryReplayBundle,
    QueryRequest,
    QueryRunStatus,
    QueryTraceBundle,
    QueryTraceReview,
    SupportState,
)
from doc_forge.query.review import (
    QueryCitationReview,
    QueryRunReviewSummary,
    QueryTraceTimingSummary,
)


class _FakeReviewArtifacts:
    def __init__(
        self,
        *,
        summary: QueryRunReviewSummary,
        trace: QueryTraceReview,
        citations: QueryCitationReview | None,
        replay: QueryReplayBundle,
    ) -> None:
        self.summary = summary
        self.trace = trace
        self.citations = citations
        self.replay = replay


class _FakeReviewService:
    def __init__(
        self,
        *,
        summary: QueryRunReviewSummary,
        trace: QueryTraceReview,
        citations: QueryCitationReview | None,
    ) -> None:
        self._summary = summary
        self._trace = trace
        self._citations = citations

    def get_query_summary(self, query_id: str) -> QueryRunReviewSummary:
        assert query_id == self._summary.query_id
        return self._summary

    def get_query_trace_review(self, query_id: str) -> QueryTraceReview:
        assert query_id == self._trace.summary.query_id
        return self._trace

    def get_query_citations(self, query_id: str) -> QueryCitationReview:
        assert query_id == self._summary.query_id
        if self._citations is None:
            raise LookupError(query_id)
        return self._citations


class _FakeReplayService:
    def __init__(self, bundle: QueryReplayBundle) -> None:
        self._bundle = bundle

    def build_bundle(self, query_id: str) -> QueryReplayBundle:
        assert query_id == self._bundle.query_id
        return self._bundle


_DEFAULT_CITATIONS = object()


def _build_fake_review_artifacts(
    *,
    query_id: str,
    citations: QueryCitationReview | None | object = _DEFAULT_CITATIONS,
    include_final_artifacts: bool = True,
) -> _FakeReviewArtifacts:
    submitted_at = datetime(2026, 3, 13, 4, 0, tzinfo=UTC)
    summary = QueryRunReviewSummary(
        query_id=query_id,
        workspace_id="ws-1",
        question="Where is the latency target defined?",
        status=QueryRunStatus.SUCCEEDED,
        submitted_at=submitted_at,
        completed_at=submitted_at,
        policy_snapshot=QueryPolicyDefaults.build().model_dump(mode="json"),
        support_state=SupportState.SUFFICIENT,
        answer_mode=AnswerMode.DIRECT_ANSWER,
        has_answer=True,
        trace_summary=QueryTraceTimingSummary(trace_count=8, total_duration_ms=12, stages=[]),
    )
    final_artifacts = (
        FinalQueryArtifacts(
            answer=AnswerDraft(
                answer_text="The target is under 2.5 seconds median latency.",
                grounded_evidence_set_ids=["es-1"],
                generator_version="answer_generation.deterministic.v1",
            ),
            citations=CitationBundle(
                citations=[
                    CitationRecord(
                        evidence_set_id="es-1",
                        support_role=CitationSupportRole.PRIMARY,
                        source_reference=SourceReference(
                            doc_id="research-notes-1",
                            document_title="Research Notes 1",
                            snippet="under 2.5 seconds median latency",
                            heading_path=["2. Study Context"],
                            page_label="p. 2",
                        ),
                    )
                ],
                material_doc_ids=["research-notes-1"],
            ),
            support_state=SupportState.SUFFICIENT,
            answer_mode=AnswerMode.DIRECT_ANSWER,
        )
        if include_final_artifacts
        else None
    )
    trace = QueryTraceReview(
        summary=summary,
        trace_bundle=QueryTraceBundle(query_id=query_id, run_status=QueryRunStatus.SUCCEEDED),
        final_artifacts=final_artifacts,
    )
    replay = QueryReplayBundle(
        query_id=query_id,
        request=QueryRequest(
            question="Where is the latency target defined?",
            workspace_id="ws-1",
        ),
        policy=QueryPolicyDefaults.build(),
        trace_bundle=QueryTraceBundle(query_id=query_id, run_status=QueryRunStatus.SUCCEEDED),
    )
    default_citations = QueryCitationReview(
        query_id=query_id,
        support_state=SupportState.SUFFICIENT,
        answer_mode=AnswerMode.DIRECT_ANSWER,
        citations=CitationBundle(citations=[], material_doc_ids=["research-notes-1"]),
    )
    if citations is _DEFAULT_CITATIONS:
        resolved_citations: QueryCitationReview | None = default_citations
    else:
        assert citations is None or isinstance(citations, QueryCitationReview)
        resolved_citations = citations
    return _FakeReviewArtifacts(
        summary=summary,
        trace=trace,
        citations=resolved_citations,
        replay=replay,
    )


def _build_collector(
    *,
    repo_root: Path,
    query_id: str = "qry-123",
    citations: QueryCitationReview | None | object = _DEFAULT_CITATIONS,
    include_final_artifacts: bool = True,
) -> QueryContextCollector:
    artifacts = _build_fake_review_artifacts(
        query_id=query_id,
        citations=citations,
        include_final_artifacts=include_final_artifacts,
    )
    return QueryContextCollector(
        review_service=_FakeReviewService(
            summary=artifacts.summary,
            trace=artifacts.trace,
            citations=artifacts.citations,
        ),
        replay_service=_FakeReplayService(artifacts.replay),
        repo_root=repo_root,
        context_root=repo_root / "data" / "context",
        log_root=repo_root / "data" / "logs",
    )


def _write_e2e_logs(repo_root: Path, *, query_id: str) -> Path:
    scenario_dir = repo_root / "data" / "logs" / "e2e" / "runs" / "sess-1" / "scenario-1"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    (scenario_dir / "metadata.json").write_text(
        json.dumps(
            {
                "test_id": "e2e/test_query_runtime_smoke.py::test_query_context_bundle",
                "session_id": "sess-1",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    api_lines = [
        json.dumps(
            {
                "ts": "2026-03-13T04:00:00Z",
                "event": "query.run.started",
                "query_id": query_id,
                "workspace_id": "ws-1",
                "service": "doc_forge-api",
                "environment": "prod",
            }
        ),
        json.dumps(
            {
                "ts": "2026-03-13T04:00:01Z",
                "event": "review.trace.loaded",
                "query_id": query_id,
                "service": "doc_forge-api",
                "environment": "prod",
            }
        ),
    ]
    worker_lines = [
        json.dumps(
            {
                "ts": "2026-03-13T03:59:59Z",
                "event": "worker.run_next.invoked",
                "service": "doc_forge-worker",
                "environment": "prod",
            }
        )
    ]
    (scenario_dir / "api.jsonl").write_text("\n".join(api_lines) + "\n", encoding="utf-8")
    (scenario_dir / "worker.jsonl").write_text("\n".join(worker_lines) + "\n", encoding="utf-8")
    return scenario_dir


def test_collect_query_context_writes_complete_bundle(tmp_path) -> None:
    repo_root = tmp_path
    query_id = "qry-complete"
    _write_e2e_logs(repo_root, query_id=query_id)
    collector = _build_collector(repo_root=repo_root, query_id=query_id)

    collected = collector.collect(
        query_id,
        extras=QueryContextCollectionExtras(
            source_kind=QueryContextSourceKind.EVAL,
            case_id="lookup_rn1_001",
            query_response_payload={"query_id": query_id, "answer": {"answer_text": "ok"}},
            eval_result_payload={"overall_trust_outcome": "trustworthy"},
            execution_metadata_payload={"query_id": query_id, "workspace_id": "ws-1"},
        ),
    )

    manifest = collected.manifest
    assert manifest.source_kind is QueryContextSourceKind.EVAL
    assert manifest.run_id == "sess-1"
    assert manifest.test_id == "e2e/test_query_runtime_smoke.py::test_query_context_bundle"
    assert manifest.case_id == "lookup_rn1_001"
    assert manifest.environment == "prod"
    assert manifest.assets.summary == "summary.json"
    assert manifest.assets.citations == "citations.json"
    assert manifest.assets.trace == "trace.json"
    assert manifest.assets.replay == "replay.json"
    assert manifest.assets.query_response == "query-response.json"
    assert manifest.assets.eval_result == "eval-result.json"
    assert manifest.assets.execution_metadata == "execution-metadata.json"
    assert manifest.assets.query_events == "logs/query-events.jsonl"
    assert manifest.evaluator_outcome == "trustworthy"
    assert manifest.missing_assets == []
    assert (collected.bundle_root / "logs" / "api.jsonl").is_symlink()
    assert (collected.bundle_root / "logs" / "worker.jsonl").is_symlink()
    assert (collected.bundle_root / "logs" / "query-events.jsonl").exists()


def test_collect_query_context_reconstructs_query_response_for_non_eval_bundle(tmp_path) -> None:
    repo_root = tmp_path
    query_id = "qry-runtime"
    _write_e2e_logs(repo_root, query_id=query_id)
    collector = _build_collector(repo_root=repo_root, query_id=query_id)

    collected = collector.collect(query_id)

    manifest = collected.manifest
    assert manifest.assets.query_response == "query-response.json"
    assert "query_response" not in manifest.missing_assets
    query_response = json.loads(
        (collected.bundle_root / "query-response.json").read_text(encoding="utf-8")
    )
    assert query_response["query_id"] == query_id
    assert query_response["support_state"] == "sufficient"
    assert query_response["answer_mode"] == "direct_answer"
    assert (
        query_response["message"]
        == "query answer completed with grounded generation and rendered citations"
    )
    assert (
        query_response["answer"]["answer_text"] == "The target is under 2.5 seconds median latency."
    )
    citation = query_response["citations"]["citations"][0]
    assert citation["evidence_set_id"] == "es-1"
    assert citation["support_role"] == "primary"
    assert citation["source_reference"]["doc_id"] == "research-notes-1"
    assert citation["source_reference"]["document_title"] == "Research Notes 1"
    assert citation["source_reference"]["snippet"] == "under 2.5 seconds median latency"


def test_collect_query_context_marks_missing_optional_assets(tmp_path) -> None:
    repo_root = tmp_path
    collector = _build_collector(
        repo_root=repo_root,
        query_id="qry-missing",
        citations=None,
        include_final_artifacts=False,
    )

    collected = collector.collect("qry-missing")

    assert collected.manifest.log_assets == []
    assert set(collected.manifest.missing_assets) == {
        "api_log",
        "citations",
        "eval_result",
        "execution_metadata",
        "query_events",
        "query_response",
        "worker_log",
    }


def test_load_manifest_round_trips_written_bundle(tmp_path) -> None:
    repo_root = tmp_path
    query_id = "qry-roundtrip"
    _write_e2e_logs(repo_root, query_id=query_id)
    collector = _build_collector(repo_root=repo_root, query_id=query_id)
    collected = collector.collect(query_id)

    loaded = collector.load_manifest(query_id)

    assert isinstance(collected, CollectedQueryContext)
    assert loaded == collected.manifest
    assert (
        QueryContextManifest.model_validate_json(
            collected.manifest_path.read_text(encoding="utf-8")
        )
        == collected.manifest
    )
