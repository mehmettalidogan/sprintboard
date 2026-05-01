"""
Project service for analysis and risk calculation.

Sprint 2 değişiklikleri / Sprint 2 changes:
    - calculate_risk_score() artık saf hesaplama mantığını RiskCalculator'a
      devreder; API sözleşmesi ve dönüş şeması değişmeden kalır.
      calculate_risk_score() now delegates pure computation to RiskCalculator;
      the API contract and return schema remain unchanged.

    - calculate_member_risk_scores() yeni metot olarak eklendi; proje
      görevleri üzerinden kişi bazlı risk skorları üretir.
      calculate_member_risk_scores() added as a new method, producing
      per-member risk scores from project tasks.

    - _build_tasks_df() ve _build_sprints_df() özel yardımcıları ORM →
      DataFrame dönüşümünü tek bir yerde toplar (DRY).
      _build_tasks_df() and _build_sprints_df() private helpers centralise
      ORM → DataFrame conversion in one place (DRY).

    Mevcut kod değiştirilmedi; yalnızca yorum satırları ve yeni metodlar eklendi.
    Existing code was not changed; only comments and new methods were added.
"""

from __future__ import annotations

import uuid
from typing import List

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sprint import Sprint
from app.models.task import Task
from app.schemas.project_analysis import MemberRiskScore, ProjectRiskScore, ProjectTaskAnalysis

# Sprint 2: Saf hesaplama motorunu içe aktar (Bağımlılık Tersine Çevirme — DIP)
# Sprint 2: Import the pure computation engine (Dependency Inversion — DIP)
from app.services.risk_calculator import RiskCalculator


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_project_analysis(self, project_id: uuid.UUID) -> ProjectTaskAnalysis:
        """Fetch total task counts separated by status for a project."""
        query = (
            select(Task.status, func.count().label("count"))
            .join(Sprint)
            .where(Sprint.project_id == project_id)
            .group_by(Task.status)
        )
        result = await self.db.execute(query)
        rows = result.all()

        counts = {"completed": 0, "in_progress": 0, "delayed": 0, "pending": 0}
        total = 0
        for status, count in rows:
            clean_status = status.lower().strip()
            if clean_status in counts:
                counts[clean_status] = count
            else:
                counts["pending"] += count
            total += count

        return ProjectTaskAnalysis(
            project_id=project_id,
            total_tasks=total,
            completed_tasks=counts["completed"],
            in_progress_tasks=counts["in_progress"],
            delayed_tasks=counts["delayed"],
            pending_tasks=counts["pending"],
        )

    async def calculate_risk_score(self, project_id: uuid.UUID) -> ProjectRiskScore:
        """
        Pandas kullanarak proje risk skorunu hesaplar.
        Calculate project risk score using pandas.

        Sprint 2: Hesaplama mantığı RiskCalculator'a devredildi.
        Sprint 2: Computation logic delegated to RiskCalculator.

        Dönüş şeması değişmedi — mevcut API sözleşmesi korunuyor (OCP).
        Return schema unchanged — existing API contract preserved (OCP).
        """
        # Görev ve sprint verilerini ORM'den DataFrame'e dönüştür (DRY yardımcılar)
        # Convert task and sprint data from ORM to DataFrame (DRY helpers)
        tasks = await self._fetch_project_tasks(project_id)

        if not tasks:
            return ProjectRiskScore(
                project_id=project_id,
                risk_score=0.0,
                risk_level="Low",
                details={"message": "No tasks found in project sprints."},
            )

        # Görevleri DataFrame'e dönüştür / Convert tasks to DataFrame
        tasks_df = self._build_tasks_df(tasks)

        # Sprint zamanlaması analizi için sprint satırlarını da al
        # Also fetch sprint rows for sprint timing analysis
        sprints_df = await self._build_sprints_df(project_id)

        # Saf hesaplama motorunu çalıştır / Run the pure computation engine
        result = RiskCalculator().load(tasks_df, sprints_df).calculate_project_risk()

        # Sprint zamanlama risklerini ayrıntılar sözlüğüne ekle
        # Append sprint timing risks to the details dictionary
        timing = RiskCalculator().load(tasks_df, sprints_df).get_sprint_timing_risk()

        details = {
            "incomplete_ratio_score": result.incomplete_ratio_score,
            "deadline_risk_score": result.deadline_risk_score,
            "workload_risk_score": result.workload_risk_score,
            "total_tasks": result.total_tasks,
            "incomplete_tasks": result.incomplete_tasks,
            # Sprint zamanlama sözlüğü — boş olabilir
            # Sprint timing dict — may be empty if no sprints
            "sprint_timing": timing,
        }

        return ProjectRiskScore(
            project_id=project_id,
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            details=details,
        )

    async def calculate_member_risk_scores(
        self, project_id: uuid.UUID
    ) -> List[MemberRiskScore]:
        """
        Proje görevleri üzerinden kişi bazlı risk skorları hesaplar.
        Calculate per-member risk scores from project tasks.

        Sprint 2'de eklendi — mevcut metodları değiştirmez (OCP).
        Added in Sprint 2 — does not modify existing methods (OCP).
        """
        tasks = await self._fetch_project_tasks(project_id)

        if not tasks:
            return []

        tasks_df = self._build_tasks_df(tasks)
        sprints_df = await self._build_sprints_df(project_id)

        # Kişi bazlı sonuçları hesapla / Compute per-member results
        member_results = (
            RiskCalculator().load(tasks_df, sprints_df).calculate_member_risks()
        )

        # Pydantic şemasına dönüştür / Convert to Pydantic schema
        return [
            MemberRiskScore(
                assignee_id=r.assignee_id,
                risk_score=r.risk_score,
                risk_level=r.risk_level,
                assigned_tasks=r.assigned_tasks,
                incomplete_tasks=r.incomplete_tasks,
                overdue_tasks=r.overdue_tasks,
                deadline_risk_score=r.deadline_risk_score,
                workload_score=r.workload_score,
            )
            for r in member_results
        ]

    # ── Özel ORM yardımcıları / Private ORM helpers (DRY) ─────────────────────

    async def _fetch_project_tasks(self, project_id: uuid.UUID) -> list:
        """
        Bir projeye ait tüm Task ORM nesnelerini veritabanından çeker.
        Fetch all Task ORM objects belonging to a project from the database.

        Bu yardımcı, task sorgusunu tek bir yerde toplar (DRY).
        This helper centralises the task query in one place (DRY).
        """
        query = select(Task).join(Sprint).where(Sprint.project_id == project_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    def _build_tasks_df(self, tasks: list) -> pd.DataFrame:
        """
        ORM Task nesnelerini RiskCalculator'ın beklediği DataFrame'e dönüştürür.
        Convert ORM Task objects to the DataFrame expected by RiskCalculator.

        sprint_id sütunu sprint zamanlama analizi için dahil edilmiştir.
        sprint_id column is included for sprint timing analysis.
        """
        return pd.DataFrame([
            {
                "id": str(t.id),
                "sprint_id": str(t.sprint_id),
                "status": t.status,
                "deadline": t.deadline,
                "assignee_id": str(t.assignee_id) if t.assignee_id else None,
            }
            for t in tasks
        ])

    async def _build_sprints_df(self, project_id: uuid.UUID) -> pd.DataFrame:
        """
        Bir projeye ait Sprint ORM nesnelerini RiskCalculator DataFrame'ine dönüştürür.
        Convert Sprint ORM objects for a project to the RiskCalculator DataFrame.

        Yalnızca aktif (silinmemiş) sprintler dahil edilir.
        Only active (non-deleted) sprints are included.
        """
        query = (
            select(Sprint)
            .where(Sprint.project_id == project_id)
            .where(Sprint.deleted_at.is_(None))
        )
        result = await self.db.execute(query)
        sprints = result.scalars().all()

        if not sprints:
            return pd.DataFrame()

        return pd.DataFrame([
            {
                "id": str(s.id),
                "start_date": s.start_date,
                "end_date": s.end_date,
                "project_id": str(s.project_id),
            }
            for s in sprints
        ])
