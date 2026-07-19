"""structured memory

Revision ID: 0002_structured_memory
Revises: 0001_initial
Create Date: 2026-07-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_structured_memory"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("characters") as batch_op:
        batch_op.add_column(sa.Column("period_stage", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("period_summary", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("period_source_chapter_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_characters_period_source_chapter_id_chapters",
            "chapters",
            ["period_source_chapter_id"],
            ["id"],
        )
        batch_op.create_index("ix_characters_period_source_chapter_id", ["period_source_chapter_id"])

    op.create_table(
        "story_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("source_chapter_id", sa.Integer(), sa.ForeignKey("chapters.id"), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("characters", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("consequence", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_story_events_project_id", "story_events", ["project_id"])
    op.create_index("ix_story_events_source_chapter_id", "story_events", ["source_chapter_id"])

    op.create_table(
        "world_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("source_chapter_id", sa.Integer(), sa.ForeignKey("chapters.id"), nullable=True),
        sa.Column("rule", sa.Text(), nullable=False),
        sa.Column("limitation", sa.Text(), nullable=True),
        sa.Column("exception", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_world_rules_project_id", "world_rules", ["project_id"])
    op.create_index("ix_world_rules_source_chapter_id", "world_rules", ["source_chapter_id"])


def downgrade() -> None:
    op.drop_index("ix_world_rules_source_chapter_id", table_name="world_rules")
    op.drop_index("ix_world_rules_project_id", table_name="world_rules")
    op.drop_table("world_rules")

    op.drop_index("ix_story_events_source_chapter_id", table_name="story_events")
    op.drop_index("ix_story_events_project_id", table_name="story_events")
    op.drop_table("story_events")

    with op.batch_alter_table("characters") as batch_op:
        batch_op.drop_index("ix_characters_period_source_chapter_id")
        batch_op.drop_constraint("fk_characters_period_source_chapter_id_chapters", type_="foreignkey")
        batch_op.drop_column("period_source_chapter_id")
        batch_op.drop_column("period_summary")
        batch_op.drop_column("period_stage")
