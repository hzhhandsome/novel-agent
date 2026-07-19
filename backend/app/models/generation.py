from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GenerationTaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    paused = "paused"
    failed = "failed"
    completed = "completed"


class GenerationTaskStepStatus(str, Enum):
    pending = "pending"
    running = "running"
    failed = "failed"
    completed = "completed"


class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    chapter_id: Mapped[int | None] = mapped_column(ForeignKey("chapters.id"), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(50))
    status: Mapped[GenerationTaskStatus] = mapped_column(
        SqlEnum(GenerationTaskStatus, native_enum=False),
        default=GenerationTaskStatus.pending,
        server_default=GenerationTaskStatus.pending.value,
    )
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_config_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="generation_tasks")
    chapter = relationship("Chapter", back_populates="generation_tasks")
    steps = relationship("GenerationTaskStep", back_populates="task", cascade="all, delete-orphan")
    runs = relationship("GenerationRun", back_populates="task", cascade="all, delete-orphan")
    review_findings = relationship("ReviewFinding", back_populates="task", cascade="all, delete-orphan")


class GenerationTaskStep(Base):
    __tablename__ = "generation_task_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("generation_tasks.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    status: Mapped[GenerationTaskStepStatus] = mapped_column(
        SqlEnum(GenerationTaskStepStatus, native_enum=False),
        default=GenerationTaskStepStatus.pending,
        server_default=GenerationTaskStepStatus.pending.value,
    )
    input_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    task = relationship("GenerationTask", back_populates="steps")


class GenerationRun(Base):
    __tablename__ = "generation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("generation_tasks.id"), index=True)
    prompt_package: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_config_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_usage_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task = relationship("GenerationTask", back_populates="runs")
