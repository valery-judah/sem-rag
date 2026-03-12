"""Add terminal review fields to query runs."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_query_run_review_fields"
down_revision = "0006_query_answers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add completed-at and terminal-failure fields for query review surfaces."""

    op.add_column(
        "query_runs", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("query_runs", sa.Column("terminal_failure_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove the query review fields from query runs."""

    op.drop_column("query_runs", "terminal_failure_json")
    op.drop_column("query_runs", "completed_at")
