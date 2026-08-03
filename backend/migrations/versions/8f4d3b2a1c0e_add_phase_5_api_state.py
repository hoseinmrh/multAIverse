"""add phase 5 API state

Revision ID: 8f4d3b2a1c0e
Revises: 5bd72efdd0ea
Create Date: 2026-08-01 20:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8f4d3b2a1c0e"
down_revision: str | None = "5bd72efdd0ea"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("events", sa.Column("narrative_key", sa.String(length=120), nullable=True))
    op.create_index(op.f("ix_events_narrative_key"), "events", ["narrative_key"], unique=False)
    op.add_column(
        "future_self_conversations",
        sa.Column("personality_summary", sa.Text(), nullable=True),
    )
    op.execute(
        "UPDATE future_self_conversations "
        "SET personality_summary = 'Reflective, grounded, and consistent "
        "with the stored timeline.' "
        "WHERE personality_summary IS NULL"
    )
    with op.batch_alter_table("future_self_conversations") as batch_op:
        batch_op.alter_column("personality_summary", existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("future_self_conversations") as batch_op:
        batch_op.drop_column("personality_summary")
    op.drop_index(op.f("ix_events_narrative_key"), table_name="events")
    op.drop_column("events", "narrative_key")
