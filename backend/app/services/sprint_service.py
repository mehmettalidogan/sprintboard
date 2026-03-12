"""
SprintService — Sprint kayıt ve sorgulama işlemleri.

Analiz sonuçlarını veritabanına yazar, geçmiş sprint listesini döner.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sprint import Sprint
from app.models.sprint_member_performance import SprintMemberPerformance
from app.schemas.sprint import SprintResponse


class SprintService:

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Kaydet ────────────────────────────────────────────────────────────────
    async def save_sprint(self, result: SprintResponse, user_id: str) -> Sprint:
        """Analiz sonucunu ve üye performanslarını veritabanına yazar."""

        sprint = Sprint(
            id=result.id,
            user_id=uuid.UUID(user_id),
            github_url=str(result.github_url),
            start_date=result.start_date,
            end_date=result.end_date,
            team_members=result.team_members,
            country_code=result.country_code,
            performance_score=result.performance_score,
            workload_balance_score=result.workload_balance_score,
            total_working_days=result.total_working_days,
            analysis_notes=result.analysis_notes,
        )
        self._db.add(sprint)
        await self._db.flush()

        # Üye performanslarını kaydet
        for mp in result.member_performance:
            self._db.add(
                SprintMemberPerformance(
                    sprint_id=sprint.id,
                    github_login=mp.github_login,
                    total_commits=mp.total_commits,
                    total_additions=mp.total_additions,
                    total_deletions=mp.total_deletions,
                    active_days=mp.active_days,
                    workload_share=mp.workload_share,
                )
            )

        return sprint

    # ── Geçmiş liste ──────────────────────────────────────────────────────────
    async def get_user_sprints(self, user_id: str) -> list[Sprint]:
        """Kullanıcıya ait silinmemiş sprint analizlerini yeniden eskiye sıralar."""
        result = await self._db.execute(
            select(Sprint)
            .where(
                Sprint.user_id == uuid.UUID(user_id),
                Sprint.deleted_at.is_(None),
            )
            .order_by(Sprint.created_at.desc())
        )
        return list(result.scalars().all())

    # ── Soft delete ───────────────────────────────────────────────────────────
    async def delete_sprint(self, sprint_id: str, user_id: str) -> bool:
        """
        Sprint kaydını soft delete yapar.

        Returns:
            True — silme başarılı
            False — kayıt bulunamadı veya kullanıcıya ait değil
        """
        from datetime import datetime, timezone
        result = await self._db.execute(
            select(Sprint).where(
                Sprint.id == uuid.UUID(sprint_id),
                Sprint.user_id == uuid.UUID(user_id),
                Sprint.deleted_at.is_(None),
            )
        )
        sprint = result.scalar_one_or_none()
        if not sprint:
            return False
        sprint.deleted_at = datetime.now(tz=timezone.utc)
        return True
