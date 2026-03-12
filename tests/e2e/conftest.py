from __future__ import annotations

import os
import time
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

from parity.persistence.models import (
    chunk_embeddings_table,
    chunks_table,
    documents_table,
    index_entries_table,
    lifecycle_events_table,
)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]) -> Any:
    outcome = yield
    setattr(item, f"rep_{call.when}", outcome.get_result())


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


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
    api_container: DockerContainer
    worker_container: DockerContainer
    postgres_container: PostgresContainer
    network: Network
    verbose: bool = False
    tracked_doc_ids: list[str] = field(default_factory=list)

    def client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, timeout=30.0)

    def log(self, message: str, **fields: object) -> None:
        if not self.verbose:
            return
        details = ", ".join(f"{key}={value!r}" for key, value in sorted(fields.items()))
        suffix = f" | {details}" if details else ""
        print(f"[e2e] {message}{suffix}", flush=True)

    def track_document(self, doc_id: str) -> None:
        if doc_id not in self.tracked_doc_ids:
            self.tracked_doc_ids.append(doc_id)

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
def e2e_image_tag() -> str:
    if not _docker_daemon_available():
        pytest.skip("Docker daemon is not available")
    tag = f"parity-e2e:{uuid4().hex}"
    if _env_flag("PARITY_E2E_VERBOSE"):
        print(f"[e2e] building image {tag}", flush=True)
    image = DockerImage(
        path=str(_repo_root()),
        tag=tag,
        dockerfile_path="Dockerfile",
        clean_up=False,
    )
    image.build()
    try:
        yield tag
    finally:
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
        .with_env("PARITY_ARTIFACT_ROOT", "/artifacts")
        .with_volume_mapping(str(artifact_root), "/artifacts", mode="rw")
    )
    runtime_user = _runtime_user()
    if runtime_user is not None:
        container = container.with_kwargs(user=runtime_user)
    verbose = _env_flag("PARITY_E2E_VERBOSE")
    if verbose:
        print(
            "[e2e] running migrations"
            f" | image_tag={image_tag!r}, artifact_root={str(artifact_root)!r}",
            flush=True,
        )
    container.start()
    try:
        result = container.get_wrapped_container().wait(timeout=60)
        status_code = int(result["StatusCode"])
        if status_code != 0:
            raise AssertionError(_format_logs("migrate", container))
    finally:
        container.stop()


def _normalize_host_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg2://"):
        return database_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def _wait_for_api(base_url: str, api_container: DockerContainer) -> None:
    deadline = time.monotonic() + 45.0
    last_error: str | None = None
    verbose = _env_flag("PARITY_E2E_VERBOSE")
    if verbose:
        print(f"[e2e] waiting for api readiness | base_url={base_url!r}", flush=True)
    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"{base_url}/readyz", timeout=2.0)
            if response.status_code == 200 and response.json() == {"status": "ok"}:
                if verbose:
                    print("[e2e] api readiness probe succeeded", flush=True)
                return
            last_error = f"unexpected response: {response.status_code} {response.text}"
        except Exception as exc:
            last_error = str(exc)
        time.sleep(0.25)
    raise AssertionError(
        f"api did not become ready: {last_error}\n{_format_logs('api', api_container)}"
    )


@pytest.fixture
def e2e_stack(
    e2e_image_tag: str,
    tmp_path: Path,
    request: pytest.FixtureRequest,
) -> RunningStack:
    verbose = _env_flag("PARITY_E2E_VERBOSE")
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    if verbose:
        print(
            "[e2e] creating test stack"
            f" | artifact_root={str(artifact_root)!r}, test_id={request.node.nodeid!r}",
            flush=True,
        )

    network = Network().create()
    postgres = (
        PostgresContainer(
            "postgres:16-alpine",
            username="parity",
            password="parity",
            dbname="parity",
            driver="psycopg",
        )
        .with_network(network)
        .with_network_aliases("pg")
    )
    postgres.start()
    database_url = "postgresql+psycopg://parity:parity@pg:5432/parity"
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
        .with_env("PARITY_ARTIFACT_ROOT", "/artifacts")
        .with_env("PORT", "8000")
        .with_volume_mapping(str(artifact_root), "/artifacts", mode="rw")
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
        .with_env("PARITY_ARTIFACT_ROOT", "/artifacts")
        .with_env("PARITY_WORKER_POLL_SECONDS", "0.1")
        .with_volume_mapping(str(artifact_root), "/artifacts", mode="rw")
    )
    if runtime_user is not None:
        worker_container = worker_container.with_kwargs(user=runtime_user)

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
        api_container=api_container,
        worker_container=worker_container,
        postgres_container=postgres,
        network=network,
        verbose=verbose,
    )
    stack.log(
        "stack ready",
        base_url=base_url,
        database_url=host_database_url,
        artifact_root=str(artifact_root),
    )
    try:
        yield stack
    finally:
        failed = bool(getattr(getattr(request.node, "rep_call", None), "failed", False))
        if failed:
            print(stack.failure_report(test_id=request.node.nodeid), flush=True)
        worker_container.stop()
        api_container.stop()
        postgres.stop()
        network.remove()
