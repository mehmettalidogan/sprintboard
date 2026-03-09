"""
Sprint ORM model for SprintBoard AI.

Maps to the `sprints` table in PostgreSQL.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import List

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Sprint(Base):
    """Represents a sprint analysis session initiated by a user."""

    __tablename__ = "sprints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    github_url: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="GitHub repository URL to analyse",
    )
    start_date: Mapped[date] = mapped_column(
        nullable=False,
        comment="Sprint start date (inclusive)",
    )
    end_date: Mapped[date] = mapped_column(
        nullable=False,
        comment="Sprint end date / deadline (inclusive)",
    )
    team_members: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=True,
        default=list,
        comment="GitHub usernames of team members to track",
    )
    country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="TR",
        comment="ISO 3166-1 alpha-2 country code for public holiday lookups",
    )
    # ── Computed / cached results ──────────────────────────────────────────────
    performance_score: Mapped[float | None] = mapped_column(
        nullable=True,
        comment="Normalised 0-100 performance score, set after analysis",
    )
    workload_balance_score: Mapped[float | None] = mapped_column(
        nullable=True,
        comment="Normalised 0-100 workload balance score, set after analysis",
    )
    analysis_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable summary from the analysis engine",
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
        return f"<Sprint id={self.id} repo={self.github_url!r}>"
