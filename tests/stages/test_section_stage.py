from __future__ import annotations

from datetime import UTC, datetime

from doc_forge._contracts import ProcessingStatus, SourceType
from doc_forge.artifacts import FilesystemArtifactStore, NormalizedArtifact, NormalizedArtifactBlock
from doc_forge.persistence import (
    DocumentJobStage,
    PersistedDocument,
    SqlDocumentRepository,
    SqlSectionRepository,
)
from doc_forge.stages.sectionize import SectionizeDocumentStage
from doc_forge.structure import SectionDerivationService


def test_markdown_section_stage_recovers_parent_child_hierarchy(
    sql_engine,
    tmp_path,
    document_job_factory,
) -> None:
    artifact_store = FilesystemArtifactStore(tmp_path / "artifacts")
    documents = SqlDocumentRepository(sql_engine)
    sections = SqlSectionRepository(sql_engine)
    doc_id = "doc-sections-md"
    documents.create(
        PersistedDocument(
            doc_id=doc_id,
            workspace_id="ws-1",
            source_type=SourceType.MARKDOWN,
            title="Distributed Notes",
            filename="notes.md",
            uploaded_at=datetime(2026, 3, 11, tzinfo=UTC),
            ingest_status=ProcessingStatus.NORMALIZED,
            storage_ref="file:///tmp/notes.md",
            raw_storage_path="raw/ws-1/doc-sections-md/source.md",
        )
    )
    artifact_store.write_normalized(
        workspace_id="ws-1",
        artifact=NormalizedArtifact(
            doc_id=doc_id,
            source_type=SourceType.MARKDOWN,
            normalizer_version="markdown-v1",
            blocks=[
                NormalizedArtifactBlock(
                    kind="heading",
                    text="Overview",
                    order_index=0,
                    heading_level=1,
                    heading_path=["Overview"],
                ),
                NormalizedArtifactBlock(
                    kind="paragraph",
                    text="Consensus keeps nodes aligned.",
                    order_index=1,
                    heading_path=["Overview"],
                ),
                NormalizedArtifactBlock(
                    kind="heading",
                    text="Retries",
                    order_index=2,
                    heading_level=2,
                    heading_path=["Overview", "Retries"],
                ),
                NormalizedArtifactBlock(
                    kind="paragraph",
                    text="Retries replace downstream artifacts.",
                    order_index=3,
                    heading_path=["Overview", "Retries"],
                ),
            ],
        ),
    )

    stage = SectionizeDocumentStage(
        documents=documents,
        sections=sections,
        artifact_store=artifact_store,
        service=SectionDerivationService(),
    )
    stage.run(
        document_job_factory(
            doc_id=doc_id,
            job_id="job-sections",
            target_stage=DocumentJobStage.SECTIONIZE,
        )
    )

    stored = sections.list_for_document(doc_id)
    assert len(stored) == 3
    assert stored[1].heading_path == ["Distributed Notes", "Overview"]
    assert stored[2].heading_path == ["Distributed Notes", "Overview", "Retries"]
    assert stored[2].parent_section_id == stored[1].section_id


def test_pdf_section_stage_falls_back_to_synthetic_sections(
    sql_engine,
    tmp_path,
    document_job_factory,
) -> None:
    artifact_store = FilesystemArtifactStore(tmp_path / "artifacts")
    documents = SqlDocumentRepository(sql_engine)
    sections = SqlSectionRepository(sql_engine)
    doc_id = "doc-sections-pdf"
    documents.create(
        PersistedDocument(
            doc_id=doc_id,
            workspace_id="ws-1",
            source_type=SourceType.PDF,
            title="Ops Guide",
            filename="ops.pdf",
            uploaded_at=datetime(2026, 3, 11, tzinfo=UTC),
            ingest_status=ProcessingStatus.NORMALIZED,
            storage_ref="file:///tmp/ops.pdf",
            raw_storage_path="raw/ws-1/doc-sections-pdf/source.pdf",
        )
    )
    artifact_store.write_normalized(
        workspace_id="ws-1",
        artifact=NormalizedArtifact(
            doc_id=doc_id,
            source_type=SourceType.PDF,
            normalizer_version="pdf-v1",
            blocks=[
                NormalizedArtifactBlock(
                    kind="paragraph",
                    text="Sparse text from page one.",
                    order_index=0,
                    heading_path=[],
                    page_number=1,
                ),
                NormalizedArtifactBlock(
                    kind="paragraph",
                    text="Sparse text from page two.",
                    order_index=1,
                    heading_path=[],
                    page_number=2,
                ),
            ],
            meta={"section_fallback": "synthetic_required"},
        ),
    )

    stage = SectionizeDocumentStage(
        documents=documents,
        sections=sections,
        artifact_store=artifact_store,
        service=SectionDerivationService(),
    )
    stage.run(
        document_job_factory(
            doc_id=doc_id,
            job_id="job-sections-pdf",
            target_stage=DocumentJobStage.SECTIONIZE,
        )
    )

    stored = sections.list_for_document(doc_id)
    assert [section.heading_path for section in stored] == [
        ["Ops Guide", "Page 1"],
        ["Ops Guide", "Page 2"],
    ]
