"""
API dependency functions for SprintBoard AI.

Centralises the reusable FastAPI `Depends(...)` callables used across
all route handlers (DB session, current user, service instances, etc.).

Following Dependency Inversion Principle: route handlers depend on these
abstractions, not on concrete service constructors.
"""

from __future__ import annotations

from typing import Annotated, AsyncGenerator

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.database import AsyncSessionLocal, get_db

# ── Database ───────────────────────────────────────────────────────────────────
DbSession = Annotated[AsyncSession, Depends(get_db)]

# ── Auth ───────────────────────────────────────────────────────────────────────
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """
    Extract and validate the JWT bearer token from the Authorization header.

    Returns the `sub` claim (user ID / email) from the decoded token.

    Raises:
        HTTPException 401: If the token is missing, expired, or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise credentials_exception
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception


CurrentUser = Annotated[str, Depends(get_current_user_id)]

# ── Service factories ──────────────────────────────────────────────────────────
async def get_github_service():
    """
    Yield a :class:`GitHubService` instance for the duration of the request.

    The service's internal httpx client is opened and closed automatically.
    """
    from app.services.github_service import GitHubService

    async with GitHubService() as svc:
        yield svc


async def get_holiday_service():
    """Yield a :class:`HolidayService` instance for the duration of the request."""
    from app.services.holiday_service import HolidayService

    async with HolidayService() as svc:
        yield svc


async def get_analysis_service(
    github=Depends(get_github_service),
    holiday=Depends(get_holiday_service),
):
    """
    Build and yield an :class:`AnalysisService` with its dependencies injected.

    Both child services are resolved first so their HTTP clients are open
    before the analysis pipeline starts.
    """
    from app.services.analysis_service import AnalysisService

    yield AnalysisService(github, holiday)

async def get_ai_planner_service():
    """Build and yield an AiPlannerService."""
    from app.services.ai_planner_service import AiPlannerService
    yield AiPlannerService()

