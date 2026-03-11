from __future__ import annotations

import pytest

from tests.helpers.imports import build_instance, call_with_supported_kwargs
from tests.helpers.builders import new_document, processing_status


pytestmark = pytest.mark.stage


INDEX_STAGE_MODULES = ["parity.stages.index"]
INDEX_STAGE_CLASSES = ["IndexStage", "IndexStageRunner"]


def _build_runner(document_repo, lifecycle_event_repo, jobs_repo, index_publication_service, chunk_repo, index_entry_repo, vector_index, fixed_now):
    return build_instance(
        INDEX_STAGE_MODULES,
        INDEX_STAGE_CLASSES,
        document_repository=document_repo,
        documents=document_repo,
        lifecycle_event_repository=lifecycle_event_repo,
        lifecycle_events=lifecycle_event_repo,
        jobs=jobs_repo,
        jobs_repository=jobs_repo,
        index_publication_service=index_publication_service,
        publisher=index_publication_service,
        chunks=chunk_repo,
        chunk_repository=chunk_repo,
        index_entries=index_entry_repo,
        index_entry_repository=index_entry_repo,
        vector_index=vector_index,
        clock=lambda: fixed_now,
        now=lambda: fixed_now,
    )


def test_index_stage_publishes_every_active_chunk(document_repo, lifecycle_event_repo, jobs_repo, index_publication_service, chunk_repo, index_entry_repo, vector_index, chunk_factory, fixed_now):
    doc = new_document(doc_id="doc_1", source_type="markdown", status=processing_status("CHUNKED"), ingest_status=processing_status("CHUNKED"))
    document_repo.create(doc)
    chunk_repo.replace_for_document("doc_1", [
        chunk_factory(chunk_id="chk_1", doc_id="doc_1", section_id="sec_1"),
        chunk_factory(chunk_id="chk_2", doc_id="doc_1", section_id="sec_1", text="another chunk"),
    ])
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, index_publication_service, chunk_repo, index_entry_repo, vector_index, fixed_now)
    call_with_supported_kwargs(runner.run, doc_id="doc_1")
    assert len(vector_index.upserts) == 2
    assert len(index_entry_repo.list_for_document("doc_1")) == 2


def test_index_stage_replaces_prior_entries_for_document_on_retry(document_repo, lifecycle_event_repo, jobs_repo, index_publication_service, chunk_repo, index_entry_repo, vector_index, chunk_factory, index_entry_factory, fixed_now):
    doc = new_document(doc_id="doc_1", source_type="markdown", status=processing_status("CHUNKED"), ingest_status=processing_status("CHUNKED"))
    document_repo.create(doc)
    chunk_repo.replace_for_document("doc_1", [chunk_factory(chunk_id="chk_1", doc_id="doc_1", section_id="sec_1")])
    index_entry_repo.replace_for_document("doc_1", [index_entry_factory(chunk_id="old", doc_id="doc_1")])
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, index_publication_service, chunk_repo, index_entry_repo, vector_index, fixed_now)
    call_with_supported_kwargs(runner.run, doc_id="doc_1")
    assert {getattr(entry, "chunk_id") for entry in index_entry_repo.list_for_document("doc_1")} == {"chk_1"}


def test_index_stage_records_failure_on_partial_publication(document_repo, lifecycle_event_repo, jobs_repo, index_publication_service, chunk_repo, index_entry_repo, vector_index, chunk_factory, fixed_now):
    doc = new_document(doc_id="doc_1", source_type="markdown", status=processing_status("CHUNKED"), ingest_status=processing_status("CHUNKED"))
    document_repo.create(doc)
    chunk_repo.replace_for_document("doc_1", [chunk_factory(chunk_id="chk_1", doc_id="doc_1", section_id="sec_1")])
    index_publication_service.raise_error = RuntimeError("publish failed")
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, index_publication_service, chunk_repo, index_entry_repo, vector_index, fixed_now)
    with pytest.raises(Exception):
        call_with_supported_kwargs(runner.run, doc_id="doc_1")
    assert document_repo.status_updates
