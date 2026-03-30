"""
User ORM model for SprintBoard AI.

Maps to the `users` table in PostgreSQL.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Platform user — owns and manages sprint analysis sessions."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="User's unique email address (used as login identifier)",
    )
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Display name",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt hashed password — plain-text is never stored",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Inactive users cannot log in",
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Superusers have access to admin endpoints",
    )
    # ── Relationships ──────────────────────────────────────────────────────────
    projects: Mapped[list["Project"]] = relationship(  # type: ignore # noqa: F821
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
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
        return f"<User id={self.id} email={self.email!r}>"
