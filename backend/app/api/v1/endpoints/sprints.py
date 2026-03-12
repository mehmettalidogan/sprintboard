"""
Sprint analysis endpoints — /api/v1/sprints
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, DbSession, get_analysis_service
from app.schemas.sprint import SprintCreate, SprintResponse
from app.schemas.common import HealthResponse
from app.services.analysis_service import AnalysisService
from app.services.sprint_service import SprintService

router = APIRouter(prefix="/sprints", tags=["Sprints"])


def get_sprint_service(db: DbSession) -> SprintService:
    return SprintService(db)


@router.get(
    "/",
    response_model=list[SprintResponse],
    status_code=status.HTTP_200_OK,
    summary="Geçmiş sprint analizleri",
    description="Giriş yapan kullanıcıya ait tüm sprint analizlerini döner.",
)
async def list_sprints(
    current_user_id: CurrentUser,
    sprint_service: SprintService = Depends(get_sprint_service),
) -> list[SprintResponse]:
    sprints = await sprint_service.get_user_sprints(current_user_id)
    return [
        SprintResponse(
            id=s.id,
            github_url=s.github_url,
            start_date=s.start_date,
            end_date=s.end_date,
            team_members=s.team_members or [],
            country_code=s.country_code,
            status="completed",
            performance_score=s.performance_score,
            workload_balance_score=s.workload_balance_score,
            total_working_days=s.total_working_days,
            analysis_notes=s.analysis_notes,
            member_performance=[],
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sprints
    ]


@router.delete(
    "/{sprint_id}",
    status_code=status.HTTP_200_OK,
    summary="Sprint sil",
    description="Sprint analizini soft delete yapar. Veri fiziksel olarak silinmez.",
)
async def delete_sprint(
    sprint_id: str,
    current_user_id: CurrentUser,
    sprint_service: SprintService = Depends(get_sprint_service),
) -> dict:
    deleted = await sprint_service.delete_sprint(sprint_id, current_user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint bulunamadı veya zaten silinmiş.",
        )
    return {"success": True, "message": "Sprint silindi."}


@router.post(
    "/analyze",
    response_model=SprintResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyse a sprint",
    description=(
        "Fetch GitHub commit data for the specified repository and date window, "
        "then compute performance and workload-balance scores for the sprint team."
    ),
)
async def analyze_sprint(
    body: SprintCreate,
    current_user_id: CurrentUser,
    analysis: AnalysisService = Depends(get_analysis_service),
    sprint_service: SprintService = Depends(get_sprint_service),
) -> SprintResponse:
    try:
        result = await analysis.analyse_sprint(body)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Sprint analysis failed: {exc}",
        )

    # Sonucu veritabanına kaydet
    await sprint_service.save_sprint(result, user_id=current_user_id)

    return result
