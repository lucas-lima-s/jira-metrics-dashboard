"""create jira_issues

Revision ID: 0001
Revises:
Create Date: 2026-08-26 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jira_issues",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("issue_key", sa.String(), nullable=False),
        sa.Column("parent", sa.String(), nullable=True),
        sa.Column("issue_type", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("story_points", sa.Numeric(), nullable=True),
        sa.Column("created", sa.TIMESTAMP(), nullable=True),
        sa.Column("started", sa.TIMESTAMP(), nullable=True),
        sa.Column("resolved", sa.TIMESTAMP(), nullable=True),
        sa.Column("release", sa.String(), nullable=True),
        sa.Column("assignee", sa.String(), nullable=True),
        sa.Column("sprint_name", sa.String(), nullable=True),
        sa.Column("priority_id", sa.String(), nullable=True),
        sa.Column("priority_name", sa.String(), nullable=True),
        sa.Column("has_team_label", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issue_key"),
    )


def downgrade() -> None:
    op.drop_table("jira_issues")
