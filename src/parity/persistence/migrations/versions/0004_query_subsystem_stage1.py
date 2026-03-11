"""Add Stage 1 query subsystem tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_query_subsystem_stage1"
down_revision = "0003_indexing_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create durable query-run and query-snapshot tables."""

    op.create_table(
        "query_runs",
        sa.Column("query_id", sa.Text(), primary_key=True),
        sa.Column("workspace_id", sa.Text(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("policy_snapshot_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_query_runs_workspace_id", "query_runs", ["workspace_id"])

    op.create_table(
        "query_snapshots",
        sa.Column("query_id", sa.Text(), nullable=False),
        sa.Column("workspace_id", sa.Text(), nullable=False),
        sa.Column("query_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("eligible_doc_ids_json", sa.JSON(), nullable=False),
        sa.Column("retrieval_index_version", sa.Text(), nullable=True),
        sa.Column("readiness_version", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["query_id"], ["query_runs.query_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("query_id"),
    )
    op.create_index("ix_query_snapshots_workspace_id", "query_snapshots", ["workspace_id"])


def downgrade() -> None:
    """Drop Stage 1 query subsystem tables."""

    op.drop_index("ix_query_snapshots_workspace_id", table_name="query_snapshots")
    op.drop_table("query_snapshots")
    op.drop_index("ix_query_runs_workspace_id", table_name="query_runs")
    op.drop_table("query_runs")
