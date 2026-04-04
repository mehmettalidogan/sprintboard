"""
Projects router for analysis and risk-score operations.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.project_analysis import ProjectRiskScore, ProjectTaskAnalysis
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


def get_project_service(db: DbSession) -> ProjectService:
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
    description="Pandas kullanarak görev gecikme oranı, kullanıcı iş yükü ve tamamlanmama oranına göre 0-100 arası risk skoru üretir.",
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
