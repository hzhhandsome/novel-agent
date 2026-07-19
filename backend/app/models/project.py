from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    idea: Mapped[str] = mapped_column(Text)
    positioning: Mapped[str | None] = mapped_column(Text, nullable=True)
    worldview: Mapped[str | None] = mapped_column(Text, nullable=True)
    main_plot: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    foreshadowing_items = relationship("ForeshadowingItem", back_populates="project", cascade="all, delete-orphan")
    inspirations = relationship("Inspiration", back_populates="project", cascade="all, delete-orphan")
    generation_tasks = relationship("GenerationTask", back_populates="project", cascade="all, delete-orphan")
    story_events = relationship("StoryEvent", back_populates="project", cascade="all, delete-orphan")
    world_rules = relationship("WorldRule", back_populates="project", cascade="all, delete-orphan")
