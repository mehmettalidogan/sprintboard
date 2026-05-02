"""
Task ORM model for SprintBoard AI.

Maps to the `tasks` table in PostgreSQL.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Date, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Task(Base):
    """Represents a specific unit of work within a Sprint."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Task title / headline",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        comment="Task detailed description",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        comment="Current status: pending, in_progress, completed, delayed",
    )
    nlp_complexity_score: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        comment="NLP calculated task complexity score (1.0 to 5.0)",
    )
    deadline: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Target completion date",
    )
    
    # ── Foreign Keys ──────────────────────────────────────────────────────────
    sprint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sprints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The sprint this task belongs to",
    )
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="The user assigned to this task",
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    sprint: Mapped["Sprint"] = relationship(  # type: ignore # noqa: F821
        "Sprint",
        back_populates="tasks",
    )
    assignee: Mapped["User"] = relationship(  # type: ignore # noqa: F821
        "User",
        back_populates="tasks",
    )

    # ── Timestamps ─────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} sprint_id={self.sprint_id} status={self.status}>"
