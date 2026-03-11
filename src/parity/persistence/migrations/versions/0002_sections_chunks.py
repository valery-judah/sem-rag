"""Add sections and chunks tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_sections_chunks"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create section and chunk persistence tables."""

    op.create_table(
        "sections",
        sa.Column("section_id", sa.Text(), primary_key=True),
        sa.Column("doc_id", sa.Text(), nullable=False),
        sa.Column("heading_path_json", sa.JSON(), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column("parent_section_id", sa.Text(), nullable=True),
        sa.Column("heading_text", sa.Text(), nullable=True),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("source_start_offset", sa.Integer(), nullable=True),
        sa.Column("source_end_offset", sa.Integer(), nullable=True),
        sa.Column("structure_confidence", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["doc_id"], ["documents.doc_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["doc_id", "parent_section_id"],
            ["sections.doc_id", "sections.section_id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("doc_id", "section_id", name="uq_sections_doc_section"),
    )
    op.create_index("ix_sections_doc_id", "sections", ["doc_id"])

    op.create_table(
        "chunks",
        sa.Column("chunk_id", sa.Text(), primary_key=True),
        sa.Column("doc_id", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("heading_path_json", sa.JSON(), nullable=False),
        sa.Column("section_id", sa.Text(), nullable=True),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("source_start_offset", sa.Integer(), nullable=True),
        sa.Column("source_end_offset", sa.Integer(), nullable=True),
        sa.Column("lineage_json", sa.JSON(), nullable=True),
        sa.Column("debug_metadata_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["doc_id"], ["documents.doc_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["doc_id", "section_id"],
            ["sections.doc_id", "sections.section_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_chunks_doc_id", "chunks", ["doc_id"])


def downgrade() -> None:
    """Drop section and chunk persistence tables."""

    op.drop_index("ix_chunks_doc_id", table_name="chunks")
    op.drop_table("chunks")
    op.drop_index("ix_sections_doc_id", table_name="sections")
    op.drop_table("sections")
