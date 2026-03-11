"""Initial lifecycle metadata schema."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the initial lifecycle metadata tables."""

    op.create_table(
        "documents",
        sa.Column("doc_id", sa.Text(), primary_key=True),
        sa.Column("workspace_id", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingest_status", sa.Text(), nullable=False),
        sa.Column("storage_ref", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("checksum", sa.Text(), nullable=True),
        sa.Column("raw_storage_path", sa.Text(), nullable=True),
        sa.Column("failure_code", sa.Text(), nullable=True),
        sa.Column("failure_detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_workspace_id", "documents", ["workspace_id"])

    op.create_table(
        "lifecycle_events",
        sa.Column("event_id", sa.Text(), primary_key=True),
        sa.Column("doc_id", sa.Text(), nullable=False),
        sa.Column("stage", sa.Text(), nullable=False),
        sa.Column("from_status", sa.Text(), nullable=True),
        sa.Column("to_status", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failure_category", sa.Text(), nullable=True),
        sa.Column("detail_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["doc_id"], ["documents.doc_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_lifecycle_events_doc_id", "lifecycle_events", ["doc_id"])

    op.create_table(
        "document_jobs",
        sa.Column("job_id", sa.Text(), primary_key=True),
        sa.Column("doc_id", sa.Text(), nullable=False),
        sa.Column("target_stage", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("not_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["doc_id"], ["documents.doc_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_document_jobs_doc_id", "document_jobs", ["doc_id"])


def downgrade() -> None:
    """Drop the initial lifecycle metadata tables."""

    op.drop_index("ix_document_jobs_doc_id", table_name="document_jobs")
    op.drop_table("document_jobs")
    op.drop_index("ix_lifecycle_events_doc_id", table_name="lifecycle_events")
    op.drop_table("lifecycle_events")
    op.drop_index("ix_documents_workspace_id", table_name="documents")
    op.drop_table("documents")
