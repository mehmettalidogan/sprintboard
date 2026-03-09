"""
Sprint input/output Pydantic schemas for SprintBoard AI.

Defines the data contract for creating sprint analysis sessions and
receiving their results, including the deadline-based performance metrics.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


# ── Input ──────────────────────────────────────────────────────────────────────
class SprintCreate(BaseModel):
    """
    Request body for creating a new sprint analysis session.

    The user provides the GitHub repo URL, sprint date window,
    and the list of team member GitHub usernames to track.
    """

    github_url: HttpUrl = Field(
        ...,
        description="GitHub repository URL to analyse.",
        examples=["https://github.com/myorg/my-project"],
    )
    start_date: date = Field(
        ...,
        description="Sprint start date (inclusive). Format: YYYY-MM-DD",
        examples=["2025-01-06"],
    )
    end_date: date = Field(
        ...,
        description="Sprint end date / deadline (inclusive). Format: YYYY-MM-DD",
        examples=["2025-01-17"],
    )
    team_members: List[str] = Field(
        ...,
        min_length=1,
        description="GitHub usernames of team members to include in analysis.",
        examples=[["alice", "bob", "charlie"]],
    )
    country_code: str = Field(
        default="TR",
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code for public holiday calculations.",
        examples=["TR", "US", "DE"],
    )

    @field_validator("country_code", mode="before")
    @classmethod
    def normalise_country_code(cls, value: str) -> str:
        return value.upper().strip()

    @model_validator(mode="after")
    def validate_date_range(self) -> "SprintCreate":
        if self.start_date >= self.end_date:
            raise ValueError("end_date must be strictly after start_date.")
        delta = (self.end_date - self.start_date).days
        if delta > 90:
            raise ValueError("Sprint window cannot exceed 90 days.")
        return self


# ── Member performance detail ──────────────────────────────────────────────────
class MemberPerformance(BaseModel):
    """Per-member performance breakdown within a sprint."""

    github_login: str
    total_commits: int = Field(..., ge=0)
    total_additions: int = Field(..., ge=0)
    total_deletions: int = Field(..., ge=0)
    active_days: int = Field(..., ge=0, description="Number of distinct days with at least one commit")
    workload_share: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fraction of total team commits attributed to this member (0–1)",
    )


# ── Output ─────────────────────────────────────────────────────────────────────
class SprintResponse(BaseModel):
    """
    Full sprint analysis result.

    Returned immediately with *status='pending'* when the analysis job is queued,
    and later with *status='completed'* including all computed scores.
    """

    id: uuid.UUID
    github_url: str
    start_date: date
    end_date: date
    team_members: List[str]
    country_code: str
    # ── Status ────────────────────────────────────────────────────────────────
    status: str = Field(
        default="pending",
        description="Analysis lifecycle status: pending | running | completed | failed",
        examples=["completed"],
    )
    # ── Computed ──────────────────────────────────────────────────────────────
    performance_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Overall sprint performance score (0–100). Higher is better.",
    )
    workload_balance_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Team workload balance score (0–100). 100 = perfectly balanced.",
    )
    total_working_days: Optional[int] = Field(
        default=None,
        ge=0,
        description="Working days in the sprint (excludes weekends and public holidays).",
    )
    analysis_notes: Optional[str] = None
    member_performance: List[MemberPerformance] = Field(default_factory=list)
    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
