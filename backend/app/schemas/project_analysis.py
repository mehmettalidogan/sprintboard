"""
Project analysis and risk score models.

Sprint 2'de eklendi / Added in Sprint 2:
    MemberRiskScore — kişi bazlı risk skoru şeması
                      per-member risk score schema
"""
from __future__ import annotations

import uuid
from pydantic import BaseModel, Field


class ProjectTaskAnalysis(BaseModel):
    """Proje bazlı görev durum özeti / Project-level task status summary."""

    project_id: uuid.UUID
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    delayed_tasks: int
    pending_tasks: int


class ProjectRiskScore(BaseModel):
    """
    Proje bazlı risk skoru ve detayları.
    Project-level risk score and details.

    details sözlüğü Sprint 2'den itibaren sprint_timing anahtarını içerebilir.
    The details dict may include a sprint_timing key from Sprint 2 onward.
    """

    project_id: uuid.UUID
    risk_score: float = Field(..., ge=0.0, le=100.0, description="0-100 arası risk skoru / 0-100 risk score")
    risk_level: str = Field(..., description='"Low" | "Medium" | "High"')
    details: dict


class MemberRiskScore(BaseModel):
    """
    Tek bir ekip üyesi için hesaplanan risk skoru ve detayları.
    Risk score and details computed for a single team member.

    Sprint 2'de eklendi / Added in Sprint 2.
    """

    assignee_id: str = Field(..., description="Görevin atandığı kullanıcı UUID'si / Assignee user UUID")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="0-100 arası kişisel risk skoru / 0-100 member risk score")
    risk_level: str = Field(..., description='"Low" | "Medium" | "High"')
    assigned_tasks: int = Field(..., description="Kişiye atanmış toplam görev sayısı / Total tasks assigned to this member")
    incomplete_tasks: int = Field(..., description="Tamamlanmamış görev sayısı / Number of incomplete tasks")
    overdue_tasks: int = Field(..., description="Vadesi geçmiş görev sayısı / Number of overdue tasks")
    deadline_risk_score: float = Field(..., description="Son tarih aciliyeti alt skoru (0-40) / Deadline urgency sub-score (0-40)")
    workload_score: float = Field(..., description="İş yükü yoğunluğu alt skoru (0-20) / Workload intensity sub-score (0-20)")
