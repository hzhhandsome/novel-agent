from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChapterStatus(str, Enum):
    not_generated = "not_generated"
    generating = "generating"
    generated = "generated"
    accepted = "accepted"


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    number: Mapped[int]
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[ChapterStatus] = mapped_column(
        SqlEnum(ChapterStatus, native_enum=False),
        default=ChapterStatus.not_generated,
        server_default=ChapterStatus.not_generated.value,
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="chapters")
    generation_tasks = relationship("GenerationTask", back_populates="chapter", cascade="all, delete-orphan")
    review_findings = relationship("ReviewFinding", back_populates="chapter", cascade="all, delete-orphan")
