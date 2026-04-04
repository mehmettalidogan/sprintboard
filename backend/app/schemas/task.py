"""
Task input/output Pydantic schemas.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: str = Field(default="pending", description="Task status (e.g. pending, in_progress, completed, delayed)")
    deadline: Optional[date] = None
    assignee_id: Optional[uuid.UUID] = None


class TaskCreate(TaskBase):
    sprint_id: uuid.UUID


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[date] = None
    assignee_id: Optional[uuid.UUID] = None


class TaskOut(TaskBase):
    id: uuid.UUID
    sprint_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
