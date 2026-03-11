from __future__ import annotations

import pytest

from tests.helpers.imports import build_instance, call_with_supported_kwargs
from tests.helpers.builders import new_document, processing_status


pytestmark = pytest.mark.stage


SECTION_STAGE_MODULES = ["parity.stages.sectionize"]
SECTION_STAGE_CLASSES = ["SectionizeStage", "SectionStage", "SectionizeStageRunner"]

CHUNK_STAGE_MODULES = ["parity.stages.chunk"]
CHUNK_STAGE_CLASSES = ["ChunkStage", "ChunkStageRunner"]


def _build_section_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, structure_service, section_repo, fixed_now):
    return build_instance(
        SECTION_STAGE_MODULES,
        SECTION_STAGE_CLASSES,
        document_repository=document_repo,
        documents=document_repo,
        lifecycle_event_repository=lifecycle_event_repo,
        lifecycle_events=lifecycle_event_repo,
        jobs=jobs_repo,
        jobs_repository=jobs_repo,
        artifact_store=artifact_store,
        structure_service=structure_service,
        section_service=structure_service,
        sections=section_repo,
        section_repository=section_repo,
        clock=lambda: fixed_now,
        now=lambda: fixed_now,
    )


def _build_chunk_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, chunking_service, section_repo, chunk_repo, fixed_now):
    return build_instance(
        CHUNK_STAGE_MODULES,
        CHUNK_STAGE_CLASSES,
        document_repository=document_repo,
        documents=document_repo,
        lifecycle_event_repository=lifecycle_event_repo,
        lifecycle_events=lifecycle_event_repo,
        jobs=jobs_repo,
        jobs_repository=jobs_repo,
        artifact_store=artifact_store,
        chunking_service=chunking_service,
        chunker=chunking_service,
        sections=section_repo,
        section_repository=section_repo,
        chunks=chunk_repo,
        chunk_repository=chunk_repo,
        clock=lambda: fixed_now,
        now=lambda: fixed_now,
    )


def test_section_stage_derives_non_empty_heading_path(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, structure_service, section_repo, fixed_now):
    doc = new_document(doc_id="doc_1", source_type="markdown", status=processing_status("NORMALIZED"), ingest_status=processing_status("NORMALIZED"))
    document_repo.create(doc)
    artifact_store.write_json(path="data/normalized/doc_1/normalized.json", payload={"doc_id": "doc_1"})
    runner = _build_section_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, structure_service, section_repo, fixed_now)
    call_with_supported_kwargs(runner.run, doc_id="doc_1")
    sections = section_repo.list_for_document("doc_1")
    assert sections
    assert list(getattr(sections[0], "heading_path"))


def test_chunk_stage_replaces_existing_document_chunk_set_on_retry(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, chunking_service, section_repo, chunk_repo, section_factory, chunk_factory, fixed_now):
    doc = new_document(doc_id="doc_1", source_type="markdown", status=processing_status("NORMALIZED"), ingest_status=processing_status("NORMALIZED"))
    document_repo.create(doc)
    section_repo.replace_for_document("doc_1", [section_factory(section_id="sec_1", doc_id="doc_1")])
    chunk_repo.replace_for_document("doc_1", [chunk_factory(chunk_id="old", doc_id="doc_1", section_id="sec_1")])
    artifact_store.write_json(path="data/normalized/doc_1/normalized.json", payload={"doc_id": "doc_1"})
    runner = _build_chunk_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, chunking_service, section_repo, chunk_repo, fixed_now)
    call_with_supported_kwargs(runner.run, doc_id="doc_1")
    chunks = chunk_repo.list_for_document("doc_1")
    assert chunks
    assert {getattr(chunk, "chunk_id") for chunk in chunks} == {"chk_1"}


def test_chunk_stage_enforces_chunk_owner_link_integrity_before_advance(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, chunking_service, section_repo, chunk_repo, fixed_now):
    doc = new_document(doc_id="doc_1", source_type="markdown", status=processing_status("NORMALIZED"), ingest_status=processing_status("NORMALIZED"))
    document_repo.create(doc)
    artifact_store.write_json(path="data/normalized/doc_1/normalized.json", payload={"doc_id": "doc_1"})
    section_repo.replace_for_document("doc_1", [])
    runner = _build_chunk_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, chunking_service, section_repo, chunk_repo, fixed_now)
    with pytest.raises(Exception):
        call_with_supported_kwargs(runner.run, doc_id="doc_1")
