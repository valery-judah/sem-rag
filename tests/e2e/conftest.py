from __future__ import annotations

import os
import time
from dataclasses import dataclass
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


@dataclass
class RunningStack:
    base_url: str
    database_url: str
    artifact_root: Path
    api_container: DockerContainer
    worker_container: DockerContainer
    postgres_container: PostgresContainer
    network: Network

    def client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, timeout=30.0)

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

    def wait_for_document(
        self,
        client: httpx.Client,
        *,
        doc_id: str,
        timeout_seconds: float = 45.0,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        last_payload: dict[str, Any] | None = None
        while time.monotonic() < deadline:
            response = client.get(f"/documents/{doc_id}/status")
            response.raise_for_status()
            payload = response.json()
            last_payload = payload
            if payload["ingest_status"] in {"ready", "failed"}:
                return payload
            time.sleep(0.25)
        raise AssertionError(f"document {doc_id} did not reach a terminal state: {last_payload}")


@pytest.fixture(scope="session")
def e2e_image_tag() -> str:
    if not _docker_daemon_available():
        pytest.skip("Docker daemon is not available")
    tag = f"parity-e2e:{uuid4().hex}"
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
    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"{base_url}/readyz", timeout=2.0)
            if response.status_code == 200 and response.json() == {"status": "ok"}:
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
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()

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
    worker_container = (
        DockerContainer(e2e_image_tag)
        .with_command("worker")
        .with_network(network)
        .with_env("DATABASE_URL", database_url)
        .with_env("PARITY_ARTIFACT_ROOT", "/artifacts")
        .with_env("PARITY_WORKER_POLL_SECONDS", "0.1")
        .with_volume_mapping(str(artifact_root), "/artifacts", mode="rw")
    )

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
    )
    try:
        yield stack
    finally:
        failed = bool(getattr(getattr(request.node, "rep_call", None), "failed", False))
        if failed:
            print(_format_logs("api", api_container))
            print(_format_logs("worker", worker_container))
        worker_container.stop()
        api_container.stop()
        postgres.stop()
        network.remove()
