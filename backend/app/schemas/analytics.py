"""
Pydantic schemas for Sprint Analytics & Productivity Reporting.
"""
from __future__ import annotations

import uuid
from typing import List
from pydantic import BaseModel, Field

class MemberProductivityOut(BaseModel):
    user_id: uuid.UUID
    email: str
    github_username: str | None
    time_risk_score: float = Field(..., description="Zamanında bitirilen görevlerin tüm görevlerine oranı (0-100)")
    nlp_complexity_score: float = Field(..., description="Tamamladığı görevlerin NLP karmaşıklık ortalaması (0-100 normalize)")
    github_effort_score: float = Field(..., description="GitHub aktivitesinin hedefe (MAX_EXPECTED_GITHUB_ACTIVITY) oranı (0-100)")
    final_productivity_score: float = Field(..., description="Ağırlıklandırılmış son verimlilik puanı (0-100)")

class SprintProductivityReport(BaseModel):
    sprint_id: uuid.UUID
    total_members_analyzed: int
    member_reports: List[MemberProductivityOut]
