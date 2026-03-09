"""
Sprint analysis endpoints — /api/v1/sprints
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, DbSession, get_analysis_service
from app.schemas.sprint import SprintCreate, SprintResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/sprints", tags=["Sprints"])


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
    analysis: AnalysisService = Depends(get_analysis_service),
    # current_user: CurrentUser = None,  # uncomment to require authentication
) -> SprintResponse:
    """
    **POST /api/v1/sprints/analyze**

    Triggers the full sprint analysis pipeline:
    1. Fetches GitHub commits in the sprint window.
    2. Counts working days (public holidays + weekends excluded).
    3. Calculates per-member performance.
    4. Returns a performance score and workload balance score.
    """
    try:
        result = await analysis.analyse_sprint(body)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Sprint analysis failed: {exc}",
        )
    return result
