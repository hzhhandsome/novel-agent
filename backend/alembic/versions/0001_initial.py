"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("idea", sa.Text(), nullable=False),
        sa.Column("positioning", sa.Text(), nullable=True),
        sa.Column("worldview", sa.Text(), nullable=True),
        sa.Column("main_plot", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=13), server_default="not_generated", nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("generated_content", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chapters_project_id", "chapters", ["project_id"])
    op.create_table(
        "characters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=200), nullable=True),
        sa.Column("personality", sa.Text(), nullable=True),
        sa.Column("current_goal", sa.Text(), nullable=True),
        sa.Column("key_memories", sa.Text(), nullable=True),
        sa.Column("relationships", sa.Text(), nullable=True),
        sa.Column("writing_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_characters_project_id", "characters", ["project_id"])
    op.create_table(
        "foreshadowing_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("source_chapter_id", sa.Integer(), sa.ForeignKey("chapters.id"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=9), server_default="planted", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_foreshadowing_items_project_id", "foreshadowing_items", ["project_id"])
    op.create_index("ix_foreshadowing_items_source_chapter_id", "foreshadowing_items", ["source_chapter_id"])
    op.create_table(
        "inspirations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("applied", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_inspirations_project_id", "inspirations", ["project_id"])
    op.create_table(
        "generation_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("chapter_id", sa.Integer(), sa.ForeignKey("chapters.id"), nullable=True),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=9), server_default="pending", nullable=False),
        sa.Column("current_step", sa.String(length=100), nullable=True),
        sa.Column("error_type", sa.String(length=200), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_generation_tasks_project_id", "generation_tasks", ["project_id"])
    op.create_index("ix_generation_tasks_chapter_id", "generation_tasks", ["chapter_id"])
    op.create_table(
        "generation_task_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("generation_tasks.id"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=9), server_default="pending", nullable=False),
        sa.Column("input_snapshot", sa.JSON(), nullable=True),
        sa.Column("output_snapshot", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_generation_task_steps_task_id", "generation_task_steps", ["task_id"])
    op.create_table(
        "generation_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("generation_tasks.id"), nullable=False),
        sa.Column("prompt_package", sa.Text(), nullable=True),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column("review_result", sa.JSON(), nullable=True),
        sa.Column("accepted", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_generation_runs_task_id", "generation_runs", ["task_id"])
    op.create_table(
        "review_findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chapter_id", sa.Integer(), sa.ForeignKey("chapters.id"), nullable=False),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("generation_tasks.id"), nullable=True),
        sa.Column("problem_type", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("blocking", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_review_findings_chapter_id", "review_findings", ["chapter_id"])
    op.create_index("ix_review_findings_task_id", "review_findings", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_review_findings_task_id", table_name="review_findings")
    op.drop_index("ix_review_findings_chapter_id", table_name="review_findings")
    op.drop_table("review_findings")
    op.drop_index("ix_generation_runs_task_id", table_name="generation_runs")
    op.drop_table("generation_runs")
    op.drop_index("ix_generation_task_steps_task_id", table_name="generation_task_steps")
    op.drop_table("generation_task_steps")
    op.drop_index("ix_generation_tasks_chapter_id", table_name="generation_tasks")
    op.drop_index("ix_generation_tasks_project_id", table_name="generation_tasks")
    op.drop_table("generation_tasks")
    op.drop_index("ix_inspirations_project_id", table_name="inspirations")
    op.drop_table("inspirations")
    op.drop_index("ix_foreshadowing_items_source_chapter_id", table_name="foreshadowing_items")
    op.drop_index("ix_foreshadowing_items_project_id", table_name="foreshadowing_items")
    op.drop_table("foreshadowing_items")
    op.drop_index("ix_characters_project_id", table_name="characters")
    op.drop_table("characters")
    op.drop_index("ix_chapters_project_id", table_name="chapters")
    op.drop_table("chapters")
    op.drop_table("projects")
