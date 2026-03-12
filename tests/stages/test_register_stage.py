from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.engine import Engine

from doc_forge._contracts import ProcessingStatus, SourceType
from doc_forge.artifacts import FilesystemArtifactStore, RawArtifactRef
from doc_forge.lifecycle import LifecycleEvent
from doc_forge.persistence import (
    SqlDocumentJobRepository,
    SqlDocumentRepository,
    SqlLifecycleEventRepository,
    apply_migrations,
)
from doc_forge.stages import (
    DocumentRegistrationError,
    RegisterDocumentRequest,
    RegisterDocumentStage,
)


@pytest.fixture
def db_url(tmp_path) -> str:
    database_path = tmp_path / "register-stage.db"
    return f"sqlite+pysqlite:///{database_path}"


@pytest.fixture
def sql_engine(db_url: str) -> Iterator[Engine]:
    apply_migrations(db_url)
    engine = sa.create_engine(db_url)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
            del connection_record
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def artifact_store(tmp_path) -> FilesystemArtifactStore:
    return FilesystemArtifactStore(tmp_path / "artifacts")


@pytest.fixture
def documents(sql_engine: Engine) -> SqlDocumentRepository:
    return SqlDocumentRepository(sql_engine)


@pytest.fixture
def lifecycle_events(sql_engine: Engine) -> SqlLifecycleEventRepository:
    return SqlLifecycleEventRepository(sql_engine)


@pytest.fixture
def register_stage(
    sql_engine: Engine,
    documents: SqlDocumentRepository,
    lifecycle_events: SqlLifecycleEventRepository,
    artifact_store: FilesystemArtifactStore,
) -> RegisterDocumentStage:
    return RegisterDocumentStage(
        engine=sql_engine,
        documents=documents,
        lifecycle_events=lifecycle_events,
        artifact_store=artifact_store,
    )


@pytest.fixture
def registration_request() -> RegisterDocumentRequest:
    return RegisterDocumentRequest(
        doc_id="doc_123",
        workspace_id="ws-1",
        source_type=SourceType.MARKDOWN,
        title="Distributed Notes",
        filename="distributed-notes.md",
        uploaded_at=datetime(2026, 3, 11, 12, 0, tzinfo=UTC),
        checksum="sha256:abc123",
        content=b"# Distributed Notes\n\nConsensus starts with quorum.\n",
    )


def test_register_stage_creates_document_with_stable_identity(
    register_stage: RegisterDocumentStage,
    documents: SqlDocumentRepository,
    registration_request: RegisterDocumentRequest,
) -> None:
    created = register_stage.run(registration_request)

    loaded = documents.get(registration_request.doc_id)

    assert created == loaded
    assert loaded is not None
    assert loaded.doc_id == registration_request.doc_id
    assert loaded.workspace_id == "ws-1"
    assert loaded.ingest_status is ProcessingStatus.REGISTERED


def test_register_stage_persists_raw_artifact_linkage_and_checksum(
    register_stage: RegisterDocumentStage,
    documents: SqlDocumentRepository,
    artifact_store: FilesystemArtifactStore,
    registration_request: RegisterDocumentRequest,
) -> None:
    register_stage.run(registration_request)

    loaded = documents.get(registration_request.doc_id)

    assert loaded is not None
    assert loaded.checksum == "sha256:abc123"
    assert loaded.raw_storage_path == "raw/ws-1/doc_123/source.md"
    assert (
        loaded.storage_ref
        == artifact_store.raw_path(
            workspace_id="ws-1",
            doc_id="doc_123",
            source_type=SourceType.MARKDOWN,
        ).as_uri()
    )
    assert (
        artifact_store.read_raw(
            RawArtifactRef(
                workspace_id="ws-1",
                doc_id="doc_123",
                source_type=SourceType.MARKDOWN,
                relative_path="raw/ws-1/doc_123/source.md",
            )
        )
        == registration_request.content
    )


def test_register_stage_appends_exactly_one_register_lifecycle_event(
    register_stage: RegisterDocumentStage,
    lifecycle_events: SqlLifecycleEventRepository,
    registration_request: RegisterDocumentRequest,
) -> None:
    register_stage.run(registration_request)

    events = lifecycle_events.list_for_document(registration_request.doc_id)

    assert len(events) == 1
    assert events[0].stage.value == "register"
    assert events[0].from_status is ProcessingStatus.UPLOADED
    assert events[0].to_status is ProcessingStatus.REGISTERED


def test_register_stage_is_idempotent_for_same_intake_context(
    register_stage: RegisterDocumentStage,
    lifecycle_events: SqlLifecycleEventRepository,
    registration_request: RegisterDocumentRequest,
) -> None:
    first = register_stage.run(registration_request)
    second = register_stage.run(registration_request)

    assert second == first
    assert lifecycle_events.list_for_document(registration_request.doc_id) == [
        lifecycle_events.list_for_document(registration_request.doc_id)[0]
    ]


def test_register_stage_does_not_create_document_jobs(
    register_stage: RegisterDocumentStage,
    sql_engine: Engine,
    registration_request: RegisterDocumentRequest,
) -> None:
    jobs = SqlDocumentJobRepository(sql_engine)

    register_stage.run(registration_request)

    assert jobs.list_for_document(registration_request.doc_id) == []


def test_register_stage_database_failure_rolls_back_partial_document_row(
    sql_engine: Engine,
    documents: SqlDocumentRepository,
    artifact_store: FilesystemArtifactStore,
    registration_request: RegisterDocumentRequest,
) -> None:
    failing_events = _FailingLifecycleEventRepository()
    stage = RegisterDocumentStage(
        engine=sql_engine,
        documents=documents,
        lifecycle_events=failing_events,
        artifact_store=artifact_store,
    )

    with pytest.raises(DocumentRegistrationError):
        stage.run(registration_request)

    assert documents.get(registration_request.doc_id) is None


def test_register_stage_cleans_up_raw_artifact_after_database_failure(
    sql_engine: Engine,
    documents: SqlDocumentRepository,
    artifact_store: FilesystemArtifactStore,
    registration_request: RegisterDocumentRequest,
) -> None:
    failing_events = _FailingLifecycleEventRepository()
    stage = RegisterDocumentStage(
        engine=sql_engine,
        documents=documents,
        lifecycle_events=failing_events,
        artifact_store=artifact_store,
    )

    with pytest.raises(DocumentRegistrationError):
        stage.run(registration_request)

    assert not artifact_store.raw_path(
        workspace_id="ws-1",
        doc_id="doc_123",
        source_type=SourceType.MARKDOWN,
    ).exists()


class _FailingLifecycleEventRepository:
    def append(
        self,
        event: LifecycleEvent,
        *,
        connection=None,
    ) -> None:
        del event, connection
        raise RuntimeError("synthetic lifecycle event failure")

    def list_for_document(self, doc_id: str) -> list[LifecycleEvent]:
        del doc_id
        return []
