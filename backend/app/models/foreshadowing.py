from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ForeshadowingStatus(str, Enum):
    planted = "planted"
    advanced = "advanced"
    recovered = "recovered"


class ForeshadowingItem(Base):
    __tablename__ = "foreshadowing_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    source_chapter_id: Mapped[int | None] = mapped_column(ForeignKey("chapters.id"), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[ForeshadowingStatus] = mapped_column(
        SqlEnum(ForeshadowingStatus, native_enum=False),
        default=ForeshadowingStatus.planted,
        server_default=ForeshadowingStatus.planted.value,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="foreshadowing_items")
