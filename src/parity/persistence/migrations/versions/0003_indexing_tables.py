"""Add indexing publication and embedding tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_indexing_tables"
down_revision = "0002_sections_chunks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create index-entry and chunk-embedding tables."""

    op.create_table(
        "index_entries",
        sa.Column("chunk_id", sa.Text(), nullable=False),
        sa.Column("doc_id", sa.Text(), nullable=False),
        sa.Column("index_backend", sa.Text(), nullable=False),
        sa.Column("index_key", sa.Text(), nullable=False),
        sa.Column("index_version", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["chunks.chunk_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["doc_id"], ["documents.doc_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chunk_id"),
    )
    op.create_index("ix_index_entries_doc_id", "index_entries", ["doc_id"])

    op.create_table(
        "chunk_embeddings",
        sa.Column("chunk_id", sa.Text(), nullable=False),
        sa.Column("doc_id", sa.Text(), nullable=False),
        sa.Column("embedding_model", sa.Text(), nullable=False),
        sa.Column("embedding_vector_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["chunks.chunk_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["doc_id"], ["documents.doc_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chunk_id"),
    )
    op.create_index("ix_chunk_embeddings_doc_id", "chunk_embeddings", ["doc_id"])


def downgrade() -> None:
    """Drop index-entry and chunk-embedding tables."""

    op.drop_index("ix_chunk_embeddings_doc_id", table_name="chunk_embeddings")
    op.drop_table("chunk_embeddings")
    op.drop_index("ix_index_entries_doc_id", table_name="index_entries")
    op.drop_table("index_entries")
