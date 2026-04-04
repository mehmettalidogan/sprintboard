"""
Project analysis and risk score models.
"""
from __future__ import annotations

import uuid
from pydantic import BaseModel


class ProjectTaskAnalysis(BaseModel):
    project_id: uuid.UUID
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    delayed_tasks: int
    pending_tasks: int


class ProjectRiskScore(BaseModel):
    project_id: uuid.UUID
    risk_score: float
    risk_level: str
    details: dict
