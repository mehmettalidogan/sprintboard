"""
Planner endpoints — /api/v1/planner
"""
from __future__ import annotations
import asyncio
import uuid
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbSession, get_github_service, get_ai_planner_service
from app.schemas.planner import PlanRequest, PlanResponse
from app.services.github_service import GitHubService
from app.services.ai_planner_service import AiPlannerService
from app.models.project_plan import ProjectPlan

router = APIRouter(prefix="/planner", tags=["Planner"])

@router.post(
    "/generate",
    response_model=PlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a new Sprint Plan via AI",
)
async def generate_plan(
    body: PlanRequest,
    current_user_id: CurrentUser,
    db: DbSession,
    github: GitHubService = Depends(get_github_service),
    ai_planner: AiPlannerService = Depends(get_ai_planner_service),
) -> PlanResponse:
    """
    1. Fetch public GitHub event summaries for all requested team members asynchronously.
    2. Feed project idea and summaries to Google Gemini.
    3. Return structured agile JSON plan and save to DB.
    """
    if not body.team_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one team member must be provided."
        )

    # 1. Fetch member profiles concurrently
    async def fetch_profile(username: str) -> tuple[str, str]:
        profile_text = await github.get_user_profile(username)
        return username, profile_text

    tasks = [fetch_profile(u) for u in body.team_members]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    member_profiles: Dict[str, str] = {}
    for res in results:
        if isinstance(res, Exception):
            # Fall back to empty summary on error so it doesn't break the whole request
            continue
        username, text = res
        member_profiles[username] = text

    # 2. Call Gemini
    try:
        plan = await ai_planner.generate_plan(body, member_profiles)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI generation failed: {str(e)}"
        )

    # 3. Save to database
    try:
        db_plan = ProjectPlan(
            user_id=uuid.UUID(current_user_id),
            project_idea=body.project_idea,
            sprint_count=body.sprint_count,
            team_members=body.team_members,
            plan_data=plan.model_dump(mode="json")
        )
        db.add(db_plan)
        # We rely on FastAPI Depends(get_db) to commit
    except Exception as e:
        # We don't fail the request completely if DB save fails, just log it.
        # But raising an error might be safer depending on business logic.
        print(f"Failed to save plan to DB: {e}")

    return plan
