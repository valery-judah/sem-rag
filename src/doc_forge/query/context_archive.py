"""Query-centric filesystem context bundles for debug and evaluation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

import sqlalchemy as sa
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field

from doc_forge.identifiers import QueryId

from .persistence import (
    SqlQueryAnswerStore,
    SqlQueryRunStore,
    SqlQuerySnapshotStore,
    SqlQueryTraceStore,
)
from .replay import QueryReplayService
from .review import QueryCitationReview, QueryReviewService, QueryTraceReview


class QueryContextSourceKind(StrEnum):
    """High-level source that produced the collected query bundle."""

    COMPOSE = "compose"
    E2E = "e2e"
    EVAL = "eval"
    UNKNOWN = "unknown"


class QueryContextAssetPaths(BaseModel):
    """Relative bundle paths for persisted context assets."""

    model_config = ConfigDict(extra="forbid")

    summary: str | None = None
    citations: str | None = None
    trace: str | None = None
    replay: str | None = None
    query_response: str | None = None
    eval_result: str | None = None
    execution_metadata: str | None = None
    query_events: str | None = None


class QueryContextLogAsset(BaseModel):
    """Indexed raw log reference attached to a collected query bundle."""

    model_config = ConfigDict(extra="forbid")

    service: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    bundle_path: str | None = None
    matched_line_count: int = Field(default=0, ge=0)


class QueryContextManifest(BaseModel):
    """Filesystem manifest linking all context assets for one query."""

    model_config = ConfigDict(extra="forbid")

    query_id: QueryId = Field(min_length=1)
    workspace_id: str | None = None
    question: str | None = None
    submitted_at: datetime | None = None
    completed_at: datetime | None = None
    collected_at: datetime
    environment: str | None = None
    source_kind: QueryContextSourceKind = QueryContextSourceKind.UNKNOWN
    case_id: str | None = None
    test_id: str | None = None
    run_id: str | None = None
    support_state: str | None = None
    answer_mode: str | None = None
    evaluator_outcome: str | None = None
    assets: QueryContextAssetPaths = Field(default_factory=QueryContextAssetPaths)
    log_assets: list[QueryContextLogAsset] = Field(default_factory=lambda: [])
    missing_assets: list[str] = Field(default_factory=lambda: [])


class QueryContextCollectionExtras(BaseModel):
    """Optional metadata and payloads that are not reconstructable from persistence alone."""

    model_config = ConfigDict(extra="forbid")

    source_kind: QueryContextSourceKind | None = None
    case_id: str | None = None
    test_id: str | None = None
    run_id: str | None = None
    environment: str | None = None
    query_response_payload: dict[str, object] | None = None
    eval_result_payload: dict[str, object] | None = None
    execution_metadata_payload: dict[str, object] | None = None


@dataclass(frozen=True)
class CollectedQueryContext:
    """Result of collecting one query bundle."""

    bundle_root: Path
    manifest: QueryContextManifest

    @property
    def manifest_path(self) -> Path:
        return self.bundle_root / "manifest.json"


@dataclass(frozen=True)
class _MatchedLogFile:
    service: str
    source_path: Path
    matched_lines: list[str]


@dataclass(frozen=True)
class _LogSourceGroup:
    source_kind: QueryContextSourceKind
    run_id: str | None
    test_id: str | None
    directory: Path
    matched_files: list[_MatchedLogFile]


class QueryContextCollector:
    """Collect persisted review, replay, and log context under `data/context/queries/`."""

    def __init__(
        self,
        *,
        review_service: QueryReviewService,
        replay_service: QueryReplayService,
        repo_root: Path | None = None,
        context_root: Path | None = None,
        log_root: Path | None = None,
    ) -> None:
        self._review_service = review_service
        self._replay_service = replay_service
        self._repo_root = (repo_root or _repo_root()).resolve()
        self._context_root = (context_root or self._repo_root / "data" / "context").resolve()
        self._log_root = (log_root or self._repo_root / "data" / "logs").resolve()

    @classmethod
    def from_database_url(
        cls,
        *,
        database_url: str | None = None,
        repo_root: Path | None = None,
        context_root: Path | None = None,
        log_root: Path | None = None,
    ) -> QueryContextCollector:
        engine = sa.create_engine(database_url or _resolve_database_url())
        return cls(
            review_service=QueryReviewService(
                run_store=SqlQueryRunStore(engine),
                snapshot_store=SqlQuerySnapshotStore(engine),
                trace_store=SqlQueryTraceStore(engine),
                answer_store=SqlQueryAnswerStore(engine),
            ),
            replay_service=QueryReplayService(
                run_store=SqlQueryRunStore(engine),
                snapshot_store=SqlQuerySnapshotStore(engine),
                trace_store=SqlQueryTraceStore(engine),
                answer_store=SqlQueryAnswerStore(engine),
            ),
            repo_root=repo_root,
            context_root=context_root,
            log_root=log_root,
        )

    def collect(
        self,
        query_id: QueryId,
        *,
        extras: QueryContextCollectionExtras | None = None,
    ) -> CollectedQueryContext:
        summary = self._review_service.get_query_summary(query_id)
        trace = self._review_service.get_query_trace_review(query_id)
        replay = self._replay_service.build_bundle(query_id)
        citations = self._load_citations(query_id)
        extras = extras or QueryContextCollectionExtras()

        bundle_root = self._context_root / "queries" / query_id
        bundle_root.mkdir(parents=True, exist_ok=True)
        log_dir = bundle_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        assets = QueryContextAssetPaths()
        missing_assets: list[str] = []
        query_response_payload = extras.query_response_payload or _build_query_response_payload(
            query_id=query_id,
            trace=trace,
        )

        assets.summary = self._write_payload(
            bundle_root=bundle_root,
            filename="summary.json",
            payload=summary.model_dump(mode="json"),
        )
        assets.trace = self._write_payload(
            bundle_root=bundle_root,
            filename="trace.json",
            payload=trace.model_dump(mode="json"),
        )
        assets.replay = self._write_payload(
            bundle_root=bundle_root,
            filename="replay.json",
            payload=replay.model_dump(mode="json"),
        )

        if citations is None:
            missing_assets.append("citations")
        else:
            assets.citations = self._write_payload(
                bundle_root=bundle_root,
                filename="citations.json",
                payload=citations.model_dump(mode="json"),
            )

        if query_response_payload is None:
            missing_assets.append("query_response")
        else:
            assets.query_response = self._write_payload(
                bundle_root=bundle_root,
                filename="query-response.json",
                payload=query_response_payload,
            )

        if extras.eval_result_payload is None:
            missing_assets.append("eval_result")
        else:
            assets.eval_result = self._write_payload(
                bundle_root=bundle_root,
                filename="eval-result.json",
                payload=extras.eval_result_payload,
            )

        if extras.execution_metadata_payload is None:
            missing_assets.append("execution_metadata")
        else:
            assets.execution_metadata = self._write_payload(
                bundle_root=bundle_root,
                filename="execution-metadata.json",
                payload=extras.execution_metadata_payload,
            )

        log_groups = self._discover_log_groups(query_id)
        log_assets, query_events_path, inferred_source_kind, inferred_run_id, inferred_test_id = (
            self._materialize_logs(bundle_root=bundle_root, groups=log_groups)
        )
        if query_events_path is None:
            missing_assets.extend(["query_events", "api_log", "worker_log"])
        else:
            assets.query_events = query_events_path
            missing_assets.extend(
                asset_name
                for asset_name in ("api_log", "worker_log")
                if not any(log.service == asset_name.removesuffix("_log") for log in log_assets)
            )

        manifest = QueryContextManifest(
            query_id=query_id,
            workspace_id=summary.workspace_id,
            question=summary.question,
            submitted_at=summary.submitted_at,
            completed_at=summary.completed_at,
            collected_at=datetime.now(tz=UTC),
            environment=extras.environment or self._infer_environment(log_groups),
            source_kind=extras.source_kind or inferred_source_kind,
            case_id=extras.case_id,
            test_id=extras.test_id or inferred_test_id,
            run_id=extras.run_id or inferred_run_id,
            support_state=None if summary.support_state is None else summary.support_state.value,
            answer_mode=None if summary.answer_mode is None else summary.answer_mode.value,
            evaluator_outcome=_payload_string(extras.eval_result_payload, "overall_trust_outcome"),
            assets=assets,
            log_assets=log_assets,
            missing_assets=sorted(set(missing_assets)),
        )
        self._write_payload(
            bundle_root=bundle_root,
            filename="manifest.json",
            payload=manifest.model_dump(mode="json"),
        )
        return CollectedQueryContext(bundle_root=bundle_root, manifest=manifest)

    def load_manifest(self, query_id: QueryId) -> QueryContextManifest:
        manifest_path = self._context_root / "queries" / query_id / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"query context manifest for {query_id!r} was not found")
        return QueryContextManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))

    def render_summary(self, query_id: QueryId) -> str:
        manifest = self.load_manifest(query_id)
        bundle_root = self._context_root / "queries" / query_id
        lines = [
            f"bundle_root={bundle_root}",
            f"query_id={manifest.query_id}",
            f"workspace_id={manifest.workspace_id}",
            f"source_kind={manifest.source_kind.value}",
            f"run_id={manifest.run_id}",
            f"test_id={manifest.test_id}",
            f"case_id={manifest.case_id}",
            f"support_state={manifest.support_state}",
            f"answer_mode={manifest.answer_mode}",
            f"evaluator_outcome={manifest.evaluator_outcome}",
            "assets:",
        ]
        for label, value in manifest.assets.model_dump(mode="python").items():
            lines.append(f"  {label}={None if value is None else bundle_root / value}")
        lines.append("logs:")
        if manifest.log_assets:
            for asset in manifest.log_assets:
                resolved_bundle_path = None
                if asset.bundle_path is not None:
                    resolved_bundle_path = bundle_root / asset.bundle_path
                lines.append(
                    "  "
                    + ", ".join(
                        [
                            f"service={asset.service}",
                            f"source_path={asset.source_path}",
                            f"bundle_path={resolved_bundle_path}",
                            f"matched_line_count={asset.matched_line_count}",
                        ]
                    )
                )
        else:
            lines.append("  <none>")
        lines.append(f"missing_assets={','.join(manifest.missing_assets) or '<none>'}")
        return "\n".join(lines)

    def _load_citations(self, query_id: QueryId) -> QueryCitationReview | None:
        try:
            return self._review_service.get_query_citations(query_id)
        except LookupError:
            return None

    def _write_payload(self, *, bundle_root: Path, filename: str, payload: Any) -> str:
        path = bundle_root / filename
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path.relative_to(bundle_root).as_posix()

    def _discover_log_groups(self, query_id: QueryId) -> list[_LogSourceGroup]:
        groups: list[_LogSourceGroup] = []
        for directory in self._candidate_log_directories():
            matched_files: list[_MatchedLogFile] = []
            for service in ("api", "worker"):
                source_path = directory / f"{service}.jsonl"
                if not source_path.exists():
                    continue
                matched_lines = _matching_query_log_lines(source_path, query_id)
                if matched_lines:
                    matched_files.append(
                        _MatchedLogFile(
                            service=service,
                            source_path=source_path,
                            matched_lines=matched_lines,
                        )
                    )
            if not matched_files:
                continue
            source_kind, run_id, test_id = _classify_log_directory(directory)
            groups.append(
                _LogSourceGroup(
                    source_kind=source_kind,
                    run_id=run_id,
                    test_id=test_id,
                    directory=directory,
                    matched_files=matched_files,
                )
            )
        return groups

    def _candidate_log_directories(self) -> list[Path]:
        candidates: list[Path] = []
        compose_root = self._log_root / "compose" / "runs"
        if compose_root.exists():
            candidates.extend(path for path in compose_root.iterdir() if path.is_dir())
        e2e_root = self._log_root / "e2e" / "runs"
        if e2e_root.exists():
            for session_dir in e2e_root.iterdir():
                if not session_dir.is_dir():
                    continue
                for scenario_dir in session_dir.iterdir():
                    if not scenario_dir.is_dir() or scenario_dir.name == "session":
                        continue
                    candidates.append(scenario_dir)
        return sorted(candidates)

    def _materialize_logs(
        self,
        *,
        bundle_root: Path,
        groups: list[_LogSourceGroup],
    ) -> tuple[
        list[QueryContextLogAsset], str | None, QueryContextSourceKind, str | None, str | None
    ]:
        if not groups:
            return [], None, QueryContextSourceKind.UNKNOWN, None, None
        selected_group = groups[0]
        log_dir = bundle_root / "logs"
        events_path = log_dir / "query-events.jsonl"
        event_records: list[tuple[str, str]] = []
        log_assets: list[QueryContextLogAsset] = []

        for matched_file in selected_group.matched_files:
            link_path = log_dir / f"{matched_file.service}.jsonl"
            _refresh_symlink(latest_path=link_path, target_path=matched_file.source_path)
            relative_link = link_path.relative_to(bundle_root).as_posix()
            log_assets.append(
                QueryContextLogAsset(
                    service=matched_file.service,
                    source_path=matched_file.source_path.as_posix(),
                    bundle_path=relative_link,
                    matched_line_count=len(matched_file.matched_lines),
                )
            )
            event_records.extend(
                (_extract_timestamp(line), line) for line in matched_file.matched_lines
            )

        for service in ("api", "worker"):
            if any(asset.service == service for asset in log_assets):
                continue
            companion_path = selected_group.directory / f"{service}.jsonl"
            if not companion_path.exists():
                continue
            link_path = log_dir / f"{service}.jsonl"
            _refresh_symlink(latest_path=link_path, target_path=companion_path)
            relative_link = link_path.relative_to(bundle_root).as_posix()
            log_assets.append(
                QueryContextLogAsset(
                    service=service,
                    source_path=companion_path.as_posix(),
                    bundle_path=relative_link,
                    matched_line_count=0,
                )
            )

        event_lines = [line for _, line in sorted(event_records, key=lambda item: item[0])]
        if not event_lines:
            return (
                sorted(log_assets, key=lambda asset: asset.service),
                None,
                selected_group.source_kind,
                selected_group.run_id,
                selected_group.test_id,
            )
        events_path.write_text("\n".join(event_lines) + "\n", encoding="utf-8")
        return (
            sorted(log_assets, key=lambda asset: asset.service),
            events_path.relative_to(bundle_root).as_posix(),
            selected_group.source_kind,
            selected_group.run_id,
            selected_group.test_id,
        )

    def _infer_environment(self, groups: list[_LogSourceGroup]) -> str | None:
        for group in groups:
            for matched_file in group.matched_files:
                for line in matched_file.matched_lines:
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    environment = payload.get("environment")
                    if isinstance(environment, str) and environment:
                        return environment
        return None


def _matching_query_log_lines(path: Path, query_id: QueryId) -> list[str]:
    needle = f'"query_id": "{query_id}"'
    matched: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if needle not in line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("query_id") == query_id:
            matched.append(line)
    return matched


def _extract_timestamp(line: str) -> str:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return ""
    ts = payload.get("ts")
    return ts if isinstance(ts, str) else ""


def _classify_log_directory(
    directory: Path,
) -> tuple[QueryContextSourceKind, str | None, str | None]:
    parts = directory.parts
    if "compose" in parts and "runs" in parts:
        run_index = parts.index("runs") + 1
        return QueryContextSourceKind.COMPOSE, parts[run_index], None
    if "e2e" in parts and "runs" in parts:
        run_index = parts.index("runs") + 1
        session_id = parts[run_index]
        metadata_path = directory / "metadata.json"
        if metadata_path.exists():
            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
                metadata: dict[str, Any] = cast(dict[str, Any], data) if isinstance(data, dict) else {}
            except json.JSONDecodeError:
                metadata = {}
            test_id = metadata.get("test_id")
            if isinstance(test_id, str) and test_id:
                return QueryContextSourceKind.E2E, session_id, test_id
        return QueryContextSourceKind.E2E, session_id, directory.name
    return QueryContextSourceKind.UNKNOWN, None, None


def _refresh_symlink(*, latest_path: Path, target_path: Path) -> None:
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    if latest_path.exists() or latest_path.is_symlink():
        latest_path.unlink()
    relative_target = os.path.relpath(target_path, start=latest_path.parent)
    latest_path.symlink_to(relative_target)


def _payload_string(payload: dict[str, object] | None, key: str) -> str | None:
    if payload is None:
        return None
    value = payload.get(key)
    return value if isinstance(value, str) else None


def _build_query_response_payload(
    *,
    query_id: QueryId,
    trace: QueryTraceReview,
) -> dict[str, object] | None:
    final_artifacts = trace.final_artifacts
    if final_artifacts is None:
        return None
    return {
        "query_id": query_id,
        "answer": final_artifacts.answer.model_dump(mode="json"),
        "support_state": final_artifacts.support_state.value,
        "answer_mode": final_artifacts.answer_mode.value,
        "citations": final_artifacts.citations.model_dump(mode="json"),
        "message": "query answer completed with grounded generation and rendered citations",
    }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _resolve_database_url() -> str:
    load_dotenv()
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://doc-forge:doc-forge@localhost:5432/doc-forge",
    )
