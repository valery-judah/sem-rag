"""Add durable query stage traces."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_query_stage_traces"
down_revision = "0004_query_subsystem_stage1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the generic query stage trace table."""

    op.create_table(
        "query_stage_traces",
        sa.Column("trace_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("query_id", sa.Text(), nullable=False),
        sa.Column("stage_name", sa.Text(), nullable=False),
        sa.Column("stage_status", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["query_id"], ["query_runs.query_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_query_stage_traces_query_id", "query_stage_traces", ["query_id"])


def downgrade() -> None:
    """Drop the generic query stage trace table."""

    op.drop_index("ix_query_stage_traces_query_id", table_name="query_stage_traces")
    op.drop_table("query_stage_traces")
