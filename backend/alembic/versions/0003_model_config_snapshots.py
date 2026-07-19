"""model config snapshots

Revision ID: 0003_model_config_snapshots
Revises: 0002_structured_memory
Create Date: 2026-07-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_model_config_snapshots"
down_revision: str | None = "0002_structured_memory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("generation_tasks") as batch_op:
        batch_op.add_column(sa.Column("model_config_snapshot", sa.JSON(), nullable=True))

    with op.batch_alter_table("generation_runs") as batch_op:
        batch_op.add_column(sa.Column("model_config_snapshot", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("generation_runs") as batch_op:
        batch_op.drop_column("model_config_snapshot")

    with op.batch_alter_table("generation_tasks") as batch_op:
        batch_op.drop_column("model_config_snapshot")
