"""
ProjectPlan ORM model for SprintBoard AI.

Maps to the `project_plans` table in PostgreSQL.
Stores AI-generated sprint plans and task assignments.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, List

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProjectPlan(Base):
    """An AI-generated sprint plan for a specific project idea, owned by a user."""

    __tablename__ = "project_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner of this project plan",
    )
    project_idea: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="The original project idea/goal provided by the user",
    )
    sprint_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of sprints requested",
    )
    team_members: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="GitHub usernames involved in the plan",
    )
    plan_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="The structured JSON output produced by the LLM containing sprint assignments",
    )
    
    # -- Relationships --
    owner: Mapped["User"] = relationship()  # type: ignore # noqa: F821

    # -- Timestamps --
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
        return f"<ProjectPlan id={self.id} user={self.user_id}>"
