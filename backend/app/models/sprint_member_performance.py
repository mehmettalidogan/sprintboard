"""
SprintMemberPerformance ORM model for SprintBoard AI.

Maps to the `sprint_member_performances` table in PostgreSQL.
Stores per-member breakdown for each sprint analysis session.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SprintMemberPerformance(Base):
    """Per-member performance record linked to a sprint analysis session."""

    __tablename__ = "sprint_member_performances"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    sprint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sprints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Sprint this record belongs to",
    )
    github_login: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="GitHub username of the team member",
    )
    total_commits: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    total_additions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Lines added across all commits",
    )
    total_deletions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Lines deleted across all commits",
    )
    active_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of distinct days with at least one commit",
    )
    workload_share: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Fraction of total team commits (0-1)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SprintMemberPerformance sprint={self.sprint_id} login={self.github_login!r}>"
