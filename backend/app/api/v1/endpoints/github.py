"""
GitHub analysis endpoints — /api/v1/github
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_github_service
from app.schemas.github import GitHubAnalysisRequest, GitHubAnalysisResponse
from app.services.github_service import GitHubService, GitHubServiceError

router = APIRouter(prefix="/github", tags=["GitHub"])


@router.post(
    "/analyze",
    response_model=GitHubAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyse a GitHub repository",
    description=(
        "Fetch raw commit history from a GitHub repository and aggregate "
        "per-contributor statistics for the given date window."
    ),
)
async def analyze_repository(
    body: GitHubAnalysisRequest,
    github: GitHubService = Depends(get_github_service),
) -> GitHubAnalysisResponse:
    """
    **POST /api/v1/github/analyze**

    Fetches commits from the GitHub REST API for the specified repository
    and time range, then returns enriched contributor statistics.
    """
    try:
        result = await github.get_analysis(
            repo_url=str(body.github_url),
            since=body.since,
            until=body.until,
            branch=body.branch,
        )
    except GitHubServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    return result


@router.get(
    "/commits",
    response_model=GitHubAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch commits (query-string variant)",
    description="Convenience GET endpoint — same as POST /analyze but params via query string.",
)
async def get_commits(
    github_url: str,
    branch: str = "main",
    github: GitHubService = Depends(get_github_service),
) -> GitHubAnalysisResponse:
    """Quick read-only commit fetch without a request body."""
    try:
        return await github.get_analysis(repo_url=github_url, branch=branch)
    except GitHubServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
