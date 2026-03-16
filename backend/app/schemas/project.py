"""
Project Pydantic schemas for SprintBoard AI.

Defines the data contracts for project creation and responses.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Create ─────────────────────────────────────────────────────────────────────
class ProjectCreate(BaseModel):
    """Request body for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255, description="Name of the project")
    description: str | None = Field(default=None, description="Optional project description")


# ── Response ───────────────────────────────────────────────────────────────────
class ProjectResponse(BaseModel):
    """Public project profile."""

    id: uuid.UUID
    name: str
    description: str | None
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
