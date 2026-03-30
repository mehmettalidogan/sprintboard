"""
Pydantic schemas for the AI Sprint Planner.
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class PlanRequest(BaseModel):
    project_idea: str
    sprint_count: int
    team_members: List[str]


class TaskAssignment(BaseModel):
    title: str
    description: str
    assignee: str
    role_assigned: str


class SprintPlanPhase(BaseModel):
    sprint_number: int
    goal: str
    tasks: List[TaskAssignment]


class PlanResponse(BaseModel):
    project_idea: str
    sprint_count: int
    sprints: List[SprintPlanPhase]

    model_config = ConfigDict(from_attributes=True)
