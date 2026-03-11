"""Add durable final query answer artifacts."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_query_answers"
down_revision = "0005_query_stage_traces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the final query answer artifact table."""

    op.create_table(
        "query_answers",
        sa.Column("query_id", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("visible_limitations_json", sa.JSON(), nullable=False),
        sa.Column("should_render_citations", sa.Boolean(), nullable=False),
        sa.Column("grounded_evidence_set_ids_json", sa.JSON(), nullable=False),
        sa.Column("support_state", sa.Text(), nullable=False),
        sa.Column("qualifying_reason_codes_json", sa.JSON(), nullable=False),
        sa.Column("answer_mode", sa.Text(), nullable=False),
        sa.Column("citations_json", sa.JSON(), nullable=False),
        sa.Column("trust_failure_labels_json", sa.JSON(), nullable=False),
        sa.Column("generator_version", sa.Text(), nullable=False),
        sa.Column("renderer_version", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["query_id"], ["query_runs.query_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("query_id"),
    )


def downgrade() -> None:
    """Drop the final query answer artifact table."""

    op.drop_table("query_answers")
