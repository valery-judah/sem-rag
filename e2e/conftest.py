from __future__ import annotations

import json
import os
import re
import shutil
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4

import docker
import httpx
import pytest
import sqlalchemy as sa
from testcontainers.core.container import DockerContainer
from testcontainers.core.image import DockerImage
from testcontainers.core.network import Network
from testcontainers.postgres import PostgresContainer

from doc_forge.persistence.jobs import document_jobs_table
from doc_forge.persistence.models import (
    chunk_embeddings_table,
    chunks_table,
    documents_table,
    index_entries_table,
    lifecycle_events_table,
)
from doc_forge.query.persistence import query_runs_table


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]) -> Any:
    outcome = yield
    setattr(item, f"rep_{call.when}", outcome.get_result())


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _configure_docker_environment() -> None:
    if os.environ.get("DOCKER_HOST"):
        return
    desktop_socket = Path.home() / ".docker" / "run" / "docker.sock"
    if desktop_socket.exists():
        os.environ["DOCKER_HOST"] = f"unix://{desktop_socket}"


def _docker_daemon_available() -> bool:
    _configure_docker_environment()
    try:
        client = docker.from_env()
        client.ping()
    except Exception:
        return False
    return True


def _format_logs(label: str, container: DockerContainer) -> str:
    stdout, stderr = container.get_logs()
    combined = b"\n".join(part for part in (stdout, stderr) if part)
    text = combined.decode("utf-8", errors="replace").strip()
    return f"{label} logs:\n{text}" if text else f"{label} logs: <empty>"


def _env_flag(name: str) -> bool:
    value = os.environ.get(name, "")
    return value.lower() in {"1", "true", "yes", "on"}


def _emit_e2e_log(message: str, **fields: object) -> None:
    details = ", ".join(f"{key}={value!r}" for key, value in sorted(fields.items()))
    suffix = f" | {details}" if details else ""
    print(f"[e2e] {message}{suffix}", flush=True)


def _runtime_user() -> str | None:
    getuid = getattr(os, "getuid", None)
    getgid = getattr(os, "getgid", None)
    if getuid is None or getgid is None:
        return None
    return f"{getuid()}:{getgid()}"


@dataclass
class RunningStack:
    base_url: str
    database_url: str
    artifact_root: Path
    log_root: Path
    e2e_log_session_id: str | None
    api_container: DockerContainer
    worker_container: DockerContainer
    postgres_container: PostgresContainer
    network: Network
    verbose: bool = False
    current_test_id: str | None = None
    tracked_doc_ids: list[str] = field(default_factory=list)
    tracked_query_ids: list[str] = field(default_factory=list)
    query_debug_artifacts: list[str] = field(default_factory=list)
    query_context_artifacts: list[str] = field(default_factory=list)
    container_log_paths: dict[str, Path] = field(default_factory=dict)
    scenario_log_offsets: dict[str, int] = field(default_factory=dict)
    scenario_log_artifacts: list[str] = field(default_factory=list)

    def client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, timeout=30.0)

    def log(self, message: str, **fields: object) -> None:
        if not self.verbose:
            return
        _emit_e2e_log(message, **fields)

    def track_document(self, doc_id: str) -> None:
        if doc_id not in self.tracked_doc_ids:
            self.tracked_doc_ids.append(doc_id)

    def track_query(self, query_id: str) -> None:
        if query_id not in self.tracked_query_ids:
            self.tracked_query_ids.append(query_id)

    def record_query_debug_artifact(self, relative_path: str) -> None:
        if relative_path not in self.query_debug_artifacts:
            self.query_debug_artifacts.append(relative_path)

    def record_query_context_artifact(self, relative_path: str) -> None:
        if relative_path not in self.query_context_artifacts:
            self.query_context_artifacts.append(relative_path)

    def begin_scenario_log_capture(self, *, test_id: str) -> None:
        del test_id
        self.scenario_log_offsets = {
            service: _count_log_lines(path) for service, path in self.container_log_paths.items()
        }
        self.scenario_log_artifacts.clear()

    def archive_scenario_logs(self, *, test_id: str) -> dict[str, Path]:
        if self.e2e_log_session_id is None:
            return {}
        scenario_slug = _slugify(test_id)
        run_dir = self.log_root / "e2e" / "runs" / self.e2e_log_session_id / scenario_slug
        latest_dir = self.log_root / "e2e" / "latest" / scenario_slug
        run_dir.mkdir(parents=True, exist_ok=True)
        latest_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = run_dir / "metadata.json"
        metadata_path.write_text(
            json.dumps(
                {
                    "test_id": test_id,
                    "scenario_slug": scenario_slug,
                    "session_id": self.e2e_log_session_id,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

        archived_paths: dict[str, Path] = {}
        recorded_artifacts = [
            metadata_path.relative_to(_repo_root()).as_posix(),
        ]
        for service, source_path in self.container_log_paths.items():
            offset = self.scenario_log_offsets.get(service, 0)
            lines = _read_log_lines(source_path)
            archived_path = run_dir / f"{service}.jsonl"
            _write_log_lines(archived_path, lines[offset:])
            latest_path = latest_dir / f"{service}.jsonl"
            _refresh_symlink(latest_path=latest_path, target_path=archived_path)
            archived_paths[service] = archived_path
            recorded_artifacts.append(archived_path.relative_to(_repo_root()).as_posix())
            recorded_artifacts.append(latest_path.relative_to(_repo_root()).as_posix())

        self.scenario_log_artifacts = sorted(recorded_artifacts)
        return archived_paths

    def vector_snapshot(self, *, doc_id: str) -> dict[str, object]:
        engine = sa.create_engine(self.database_url)
        try:
            with engine.connect() as connection:
                chunk_count = connection.scalar(
                    sa.select(sa.func.count())
                    .select_from(chunks_table)
                    .where(chunks_table.c.doc_id == doc_id)
                )
                index_entry_count = connection.scalar(
                    sa.select(sa.func.count())
                    .select_from(index_entries_table)
                    .where(index_entries_table.c.doc_id == doc_id)
                )
                embedding_count = connection.scalar(
                    sa.select(sa.func.count())
                    .select_from(chunk_embeddings_table)
                    .where(chunk_embeddings_table.c.doc_id == doc_id)
                )
                sample_row = (
                    connection.execute(
                        sa.select(
                            chunk_embeddings_table.c.embedding_model,
                            chunk_embeddings_table.c.embedding_vector_json,
                        )
                        .where(chunk_embeddings_table.c.doc_id == doc_id)
                        .limit(1)
                    )
                    .mappings()
                    .first()
                )
        finally:
            engine.dispose()
        return {
            "chunk_count": int(chunk_count or 0),
            "index_entry_count": int(index_entry_count or 0),
            "embedding_count": int(embedding_count or 0),
            "sample_embedding": None if sample_row is None else dict(sample_row),
        }

    def chunk_rows(self, *, doc_id: str) -> list[dict[str, object]]:
        engine = sa.create_engine(self.database_url)
        try:
            with engine.connect() as connection:
                rows = (
                    connection.execute(
                        sa.select(
                            chunks_table.c.chunk_id,
                            chunks_table.c.text,
                            chunks_table.c.heading_path_json,
                            chunks_table.c.section_id,
                            chunks_table.c.page_start,
                            chunks_table.c.page_end,
                            chunks_table.c.source_start_offset,
                        )
                        .where(chunks_table.c.doc_id == doc_id)
                        .order_by(chunks_table.c.ordinal, chunks_table.c.chunk_id)
                    )
                    .mappings()
                    .all()
                )
        finally:
            engine.dispose()
        return [dict(row) for row in rows]

    def document_row(self, *, doc_id: str) -> dict[str, object] | None:
        engine = sa.create_engine(self.database_url)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        sa.select(documents_table).where(documents_table.c.doc_id == doc_id)
                    )
                    .mappings()
                    .first()
                )
        finally:
            engine.dispose()
        return None if row is None else dict(row)

    def lifecycle_events(self, *, doc_id: str) -> list[dict[str, object]]:
        engine = sa.create_engine(self.database_url)
        try:
            with engine.connect() as connection:
                rows = (
                    connection.execute(
                        sa.select(lifecycle_events_table)
                        .where(lifecycle_events_table.c.doc_id == doc_id)
                        .order_by(
                            lifecycle_events_table.c.occurred_at,
                            lifecycle_events_table.c.event_id,
                        )
                    )
                    .mappings()
                    .all()
                )
        finally:
            engine.dispose()
        return [dict(row) for row in rows]

    def host_artifact_path(self, container_path: str | None) -> Path | None:
        if container_path is None:
            return None
        relative = PurePosixPath(container_path).relative_to("/artifacts")
        return self.artifact_root.joinpath(*relative.parts)

    def artifact_paths_for_document(self, *, doc_id: str) -> list[str]:
        if not self.artifact_root.exists():
            return []
        matches = [
            path.relative_to(self.artifact_root).as_posix()
            for path in self.artifact_root.rglob("*")
            if path.is_file() and doc_id in path.parts
        ]
        return sorted(matches)

    def artifact_tree(self, *, limit: int = 40) -> list[str]:
        if not self.artifact_root.exists():
            return ["<artifact root does not exist>"]
        entries = [
            path.relative_to(self.artifact_root).as_posix()
            for path in sorted(self.artifact_root.rglob("*"))
            if path.is_file()
        ]
        if not entries:
            return ["<artifact root is empty>"]
        if len(entries) <= limit:
            return entries
        remaining = len(entries) - limit
        return [*entries[:limit], f"... ({remaining} more files)"]

    def describe_document(self, *, doc_id: str) -> str:
        document = self.document_row(doc_id=doc_id)
        events = self.lifecycle_events(doc_id=doc_id)
        snapshot = self.vector_snapshot(doc_id=doc_id)
        artifact_paths = self.artifact_paths_for_document(doc_id=doc_id)
        lines = [
            f"doc_id={doc_id}",
            f"document_row={document!r}",
            f"vector_snapshot={snapshot!r}",
            f"artifact_paths={artifact_paths!r}",
            "lifecycle_events:",
        ]
        if events:
            lines.extend(f"  - {event!r}" for event in events)
        else:
            lines.append("  - <none>")
        return "\n".join(lines)

    def _format_container_state(self, label: str, container: DockerContainer) -> str:
        try:
            wrapped = container.get_wrapped_container()
            wrapped.reload()
            state = wrapped.attrs.get("State", {})
            status = state.get("Status", "<unknown>")
            exit_code = state.get("ExitCode", "<unknown>")
            return f"{label} state: status={status!r}, exit_code={exit_code!r}"
        except Exception as exc:
            return f"{label} state: unavailable ({exc})"

    def failure_report(self, *, test_id: str) -> str:
        sections = [
            f"=== E2E failure report: {test_id} ===",
            f"base_url={self.base_url}",
            f"database_url={self.database_url}",
            f"artifact_root={self.artifact_root}",
            f"log_root={self.log_root}",
            self._format_container_state("api", self.api_container),
            self._format_container_state("worker", self.worker_container),
            self._format_container_state("postgres", self.postgres_container),
            "artifact tree:",
        ]
        sections.extend(f"  - {entry}" for entry in self.artifact_tree())
        if self.tracked_doc_ids:
            for doc_id in self.tracked_doc_ids:
                sections.append(f"document diagnostics:\n{self.describe_document(doc_id=doc_id)}")
        else:
            sections.append("document diagnostics:\n<no tracked documents>")
        if self.tracked_query_ids:
            sections.append(
                "query diagnostics:\n"
                + "\n".join(
                    f"  - query_id={query_id}" for query_id in sorted(self.tracked_query_ids)
                )
            )
        else:
            sections.append("query diagnostics:\n<no tracked queries>")
        if self.query_debug_artifacts:
            sections.append(
                "query debug artifacts:\n"
                + "\n".join(f"  - {artifact}" for artifact in sorted(self.query_debug_artifacts))
            )
        else:
            sections.append("query debug artifacts:\n<none>")
        if self.query_context_artifacts:
            sections.append(
                "query context bundles:\n"
                + "\n".join(f"  - {artifact}" for artifact in sorted(self.query_context_artifacts))
            )
        else:
            sections.append("query context bundles:\n<none>")
        if self.scenario_log_artifacts:
            sections.append(
                "scenario log artifacts:\n"
                + "\n".join(f"  - {artifact}" for artifact in sorted(self.scenario_log_artifacts))
            )
        else:
            sections.append("scenario log artifacts:\n<none>")
        sections.extend(
            [
                _format_logs("api", self.api_container),
                _format_logs("worker", self.worker_container),
                _format_logs("postgres", self.postgres_container),
            ]
        )
        return "\n".join(sections)

    def wait_for_document(
        self,
        client: httpx.Client,
        *,
        doc_id: str,
        timeout_seconds: float = 45.0,
    ) -> dict[str, Any]:
        self.track_document(doc_id)
        deadline = time.monotonic() + timeout_seconds
        last_payload: dict[str, Any] | None = None
        last_status: str | None = None
        while time.monotonic() < deadline:
            response = client.get(f"/documents/{doc_id}/status")
            response.raise_for_status()
            payload = response.json()
            last_payload = payload
            current_status = str(payload["ingest_status"]).upper()
            if current_status != last_status:
                self.log(
                    "document status changed",
                    doc_id=doc_id,
                    status=current_status,
                    failure_code=payload.get("failure_code"),
                )
                last_status = current_status
            if payload["ingest_status"] in {"ready", "failed"}:
                return payload
            time.sleep(0.25)
        raise AssertionError(
            f"document {doc_id} did not reach a terminal state: {last_payload}\n"
            f"{self.describe_document(doc_id=doc_id)}"
        )


@pytest.fixture(scope="session")
def e2e_image_tag() -> Iterator[str]:
    if not _docker_daemon_available():
        pytest.skip("Docker daemon is not available")
    tag = f"doc_forge-e2e:{uuid4().hex}"
    _emit_e2e_log("building e2e image", tag=tag, dockerfile="Dockerfile.e2e")
    image = DockerImage(
        path=str(_repo_root()),
        tag=tag,
        dockerfile_path="Dockerfile.e2e",
        clean_up=False,
    )
    image.build()
    _emit_e2e_log("e2e image ready", tag=tag)
    try:
        yield tag
    finally:
        _emit_e2e_log("e2e image retained", tag=tag)
        image.remove()


def _run_migrations(
    *,
    image_tag: str,
    database_url: str,
    artifact_root: Path,
    network: Network,
) -> None:
    container = (
        DockerContainer(image_tag)
        .with_command("migrate")
        .with_network(network)
        .with_env("DATABASE_URL", database_url)
        .with_env("DOC_FORGE_ARTIFACT_ROOT", "/artifacts")
        .with_volume_mapping(str(artifact_root), "/artifacts", mode="rw")
    )
    runtime_user = _runtime_user()
    if runtime_user is not None:
        container = container.with_kwargs(user=runtime_user)
    verbose = _env_flag("DOC_FORGE_E2E_VERBOSE")
    _emit_e2e_log(
        "running migrations",
        image_tag=image_tag,
        artifact_root=str(artifact_root),
    )
    container.start()
    try:
        result = container.get_wrapped_container().wait(timeout=60)
        status_code = int(result["StatusCode"])
        if status_code != 0:
            raise AssertionError(_format_logs("migrate", container))
    finally:
        container.stop()
    if verbose:
        _emit_e2e_log("migrations complete", image_tag=image_tag)


def _normalize_host_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg2://"):
        return database_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def _wait_for_api(base_url: str, api_container: DockerContainer) -> None:
    deadline = time.monotonic() + 45.0
    last_error: str | None = None
    _env_flag("DOC_FORGE_E2E_VERBOSE")
    _emit_e2e_log("waiting for api readiness", base_url=base_url)
    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"{base_url}/readyz", timeout=2.0)
            if response.status_code == 200 and response.json() == {"status": "ok"}:
                _emit_e2e_log("api readiness probe succeeded", base_url=base_url)
                return
            last_error = f"unexpected response: {response.status_code} {response.text}"
        except Exception as exc:
            last_error = str(exc)
        time.sleep(0.25)
    raise AssertionError(
        f"api did not become ready: {last_error}\n{_format_logs('api', api_container)}"
    )


def _cleanup_resource(label: str, action: Any) -> None:
    try:
        action()
        _emit_e2e_log("cleanup complete", resource=label)
    except Exception as exc:
        _emit_e2e_log("cleanup failed", resource=label, error=str(exc))


def _wait_for_idle_jobs(database_url: str, *, timeout_seconds: float = 45.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    engine = sa.create_engine(database_url)
    try:
        while time.monotonic() < deadline:
            with engine.connect() as connection:
                active_job_count = int(
                    connection.scalar(
                        sa.select(sa.func.count())
                        .select_from(document_jobs_table)
                        .where(document_jobs_table.c.status.in_(("queued", "running")))
                    )
                    or 0
                )
            if active_job_count == 0:
                return
            time.sleep(0.25)
    finally:
        engine.dispose()
    raise AssertionError(f"document jobs did not become idle within {timeout_seconds} seconds")


def _count_log_lines(path: Path) -> int:
    return len(_read_log_lines(path))


def _read_log_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _write_log_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines)
    if lines:
        text += "\n"
    path.write_text(text, encoding="utf-8")


def _refresh_symlink(*, latest_path: Path, target_path: Path) -> None:
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    if latest_path.exists() or latest_path.is_symlink():
        latest_path.unlink()
    relative_target = os.path.relpath(target_path, start=latest_path.parent)
    latest_path.symlink_to(relative_target)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return slug or "scenario"


def _clear_artifact_root(artifact_root: Path) -> None:
    artifact_root.mkdir(parents=True, exist_ok=True)
    for child in artifact_root.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
            continue
        child.unlink()


def _reset_runtime_state(stack: RunningStack) -> None:
    _wait_for_idle_jobs(stack.database_url)
    engine = sa.create_engine(stack.database_url)
    try:
        with engine.begin() as connection:
            connection.execute(sa.delete(query_runs_table))
            connection.execute(sa.delete(documents_table))
    finally:
        engine.dispose()
    _clear_artifact_root(stack.artifact_root)
    stack.tracked_doc_ids.clear()
    stack.tracked_query_ids.clear()
    stack.query_debug_artifacts.clear()
    stack.query_context_artifacts.clear()
    stack.scenario_log_offsets.clear()
    stack.scenario_log_artifacts.clear()


@pytest.fixture(scope="session")
def e2e_runtime(
    e2e_image_tag: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[RunningStack]:
    verbose = _env_flag("DOC_FORGE_E2E_VERBOSE")
    log_root = _repo_root() / "data" / "logs"
    log_root.mkdir(parents=True, exist_ok=True)
    e2e_log_session_id = uuid4().hex
    session_log_dir = log_root / "e2e" / "runs" / e2e_log_session_id / "session"
    session_log_dir.mkdir(parents=True, exist_ok=True)
    artifact_root = tmp_path_factory.mktemp("e2e-artifacts")
    artifact_root.mkdir(exist_ok=True)
    _emit_e2e_log(
        "creating session runtime",
        artifact_root=str(artifact_root),
        log_root=str(log_root),
        e2e_log_session_id=e2e_log_session_id,
    )

    network = Network().create()
    _emit_e2e_log("network created")
    postgres: PostgresContainer | None = None
    api_container: DockerContainer | None = None
    worker_container: DockerContainer | None = None
    try:
        postgres = (
            PostgresContainer(
                "postgres:16-alpine",
                username="doc_forge",
                password="doc_forge",
                dbname="doc_forge",
                driver="psycopg",
            )
            .with_network(network)
            .with_network_aliases("pg")
        )
        postgres.start()
        _emit_e2e_log("postgres started")
        database_url = "postgresql+psycopg://doc_forge:doc_forge@pg:5432/doc_forge"
        host_database_url = _normalize_host_database_url(postgres.get_connection_url())
        _run_migrations(
            image_tag=e2e_image_tag,
            database_url=database_url,
            artifact_root=artifact_root,
            network=network,
        )

        api_container = (
            DockerContainer(e2e_image_tag)
            .with_command("api")
            .with_network(network)
            .with_env("DATABASE_URL", database_url)
            .with_env("DOC_FORGE_ARTIFACT_ROOT", "/artifacts")
            .with_env("DOC_FORGE_SERVICE_NAME", "doc_forge-api")
            .with_env(
                "DOC_FORGE_JSON_LOG_PATH",
                f"/logs/e2e/runs/{e2e_log_session_id}/session/api.jsonl",
            )
            .with_env("PORT", "8000")
            .with_volume_mapping(str(artifact_root), "/artifacts", mode="rw")
            .with_volume_mapping(str(log_root), "/logs", mode="rw")
            .with_exposed_ports(8000)
        )
        runtime_user = _runtime_user()
        if runtime_user is not None:
            api_container = api_container.with_kwargs(user=runtime_user)
        worker_container = (
            DockerContainer(e2e_image_tag)
            .with_command("worker")
            .with_network(network)
            .with_env("DATABASE_URL", database_url)
            .with_env("DOC_FORGE_ARTIFACT_ROOT", "/artifacts")
            .with_env("DOC_FORGE_SERVICE_NAME", "doc_forge-worker")
            .with_env(
                "DOC_FORGE_JSON_LOG_PATH",
                f"/logs/e2e/runs/{e2e_log_session_id}/session/worker.jsonl",
            )
            .with_env("DOC_FORGE_WORKER_POLL_SECONDS", "0.1")
            .with_volume_mapping(str(artifact_root), "/artifacts", mode="rw")
            .with_volume_mapping(str(log_root), "/logs", mode="rw")
        )
        if runtime_user is not None:
            worker_container = worker_container.with_kwargs(user=runtime_user)

        _emit_e2e_log("starting api and worker containers")
        api_container.start()
        worker_container.start()

        host = api_container.get_container_host_ip()
        port = api_container.get_exposed_port(8000)
        base_url = f"http://{host}:{port}"
        _wait_for_api(base_url, api_container)

        stack = RunningStack(
            base_url=base_url,
            database_url=host_database_url,
            artifact_root=artifact_root,
            log_root=log_root,
            e2e_log_session_id=e2e_log_session_id,
            api_container=api_container,
            worker_container=worker_container,
            postgres_container=postgres,
            network=network,
            verbose=verbose,
            container_log_paths={
                "api": session_log_dir / "api.jsonl",
                "worker": session_log_dir / "worker.jsonl",
            },
        )
        stack.log(
            "session runtime ready",
            base_url=base_url,
            database_url=host_database_url,
            artifact_root=str(artifact_root),
        )
    except Exception:
        _emit_e2e_log("session runtime startup failed")
        if worker_container is not None:
            _cleanup_resource("worker container", worker_container.stop)
        if api_container is not None:
            _cleanup_resource("api container", api_container.stop)
        if postgres is not None:
            _cleanup_resource("postgres container", postgres.stop)
        _cleanup_resource("network", network.remove)
        raise
    try:
        yield stack
    finally:
        _cleanup_resource("worker container", stack.worker_container.stop)
        _cleanup_resource("api container", stack.api_container.stop)
        _cleanup_resource("postgres container", stack.postgres_container.stop)
        _cleanup_resource("network", network.remove)


@pytest.fixture
def e2e_stack(
    e2e_runtime: RunningStack,
    request: pytest.FixtureRequest,
) -> Iterator[RunningStack]:
    _emit_e2e_log("scenario setup", test_id=request.node.nodeid)
    _reset_runtime_state(e2e_runtime)
    stack = RunningStack(
        base_url=e2e_runtime.base_url,
        database_url=e2e_runtime.database_url,
        artifact_root=e2e_runtime.artifact_root,
        log_root=e2e_runtime.log_root,
        e2e_log_session_id=e2e_runtime.e2e_log_session_id,
        api_container=e2e_runtime.api_container,
        worker_container=e2e_runtime.worker_container,
        postgres_container=e2e_runtime.postgres_container,
        network=e2e_runtime.network,
        verbose=e2e_runtime.verbose,
        current_test_id=request.node.nodeid,
        container_log_paths=e2e_runtime.container_log_paths,
    )
    stack.begin_scenario_log_capture(test_id=request.node.nodeid)
    stack.log("scenario ready", test_id=request.node.nodeid)
    try:
        yield stack
    finally:
        stack.archive_scenario_logs(test_id=request.node.nodeid)
        failed = bool(getattr(getattr(request.node, "rep_call", None), "failed", False))
        _emit_e2e_log(
            "scenario complete",
            test_id=request.node.nodeid,
            status="failed" if failed else "passed",
        )
        if failed:
            print(stack.failure_report(test_id=request.node.nodeid), flush=True)
        _reset_runtime_state(e2e_runtime)
