"""
Projects router for analysis and risk-score operations.

Sprint 2'de eklendi / Added in Sprint 2:
    GET /{project_id}/member-risk-scores
        — Kişi bazlı risk skorlarını döner.
          Returns per-member risk scores.
"""

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.project_analysis import MemberRiskScore, ProjectRiskScore, ProjectTaskAnalysis
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


def get_project_service(db: DbSession) -> ProjectService:
    """ProjectService bağımlılığını enjekte eder / Inject ProjectService dependency."""
    return ProjectService(db)


@router.get(
    "/{project_id}/analysis",
    response_model=ProjectTaskAnalysis,
    status_code=status.HTTP_200_OK,
    summary="Proje genel görev analizi",
    description="Projedeki toplam görev sayılarını durumlarına (completed, pending, vs.) göre döner.",
)
async def get_analysis(
    project_id: uuid.UUID,
    current_user_id: CurrentUser,
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectTaskAnalysis:
    try:
        analysis = await project_service.get_project_analysis(project_id)
        return analysis
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis calculation failed: {exc}",
        )


@router.get(
    "/{project_id}/risk-score",
    response_model=ProjectRiskScore,
    status_code=status.HTTP_200_OK,
    summary="Proje Risk Skoru Hesaplaması",
    description=(
        "Pandas kullanarak görev gecikme oranı, Gini tabanlı iş yükü dengesizliği "
        "ve son tarih aciliyetine göre 0-100 arası proje risk skoru üretir. "
        "Sprint 2'den itibaren yanıt details.sprint_timing anahtarını içerir."
    ),
)
async def get_risk_score(
    project_id: uuid.UUID,
    current_user_id: CurrentUser,
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectRiskScore:
    try:
        risk_score = await project_service.calculate_risk_score(project_id)
        return risk_score
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk score calculation failed: {exc}",
        )


@router.get(
    "/{project_id}/member-risk-scores",
    response_model=List[MemberRiskScore],
    status_code=status.HTTP_200_OK,
    summary="Kişi Bazlı Risk Skoru Hesaplaması",
    description=(
        "Projedeki her ekip üyesi için ayrı ayrı risk skoru hesaplar. "
        "Skorlar; üyenin tamamlanmamış görev sayısına, vadesi geçmiş görevlerine "
        "ve son tarih aciliyetine göre belirlenir. "
        "Sprint 2'de eklendi."
    ),
)
async def get_member_risk_scores(
    project_id: uuid.UUID,
    current_user_id: CurrentUser,
    project_service: ProjectService = Depends(get_project_service),
) -> List[MemberRiskScore]:
    """
    Projedeki her atanan kullanıcı için kişisel risk skoru döndürür.
    Return a personal risk score for each assignee in the project.
    """
    try:
        member_scores = await project_service.calculate_member_risk_scores(project_id)
        return member_scores
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Member risk score calculation failed: {exc}",
        )
