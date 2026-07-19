"""model usage snapshots

Revision ID: 0004_model_usage_snapshots
Revises: 0003_model_config_snapshots
Create Date: 2026-07-19 11:35:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_model_usage_snapshots"
down_revision: Union[str, None] = "0003_model_config_snapshots"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("generation_runs", sa.Column("model_usage_snapshot", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("generation_runs", "model_usage_snapshot")
