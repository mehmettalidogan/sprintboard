"""
GitHub-specific input/output Pydantic schemas for SprintBoard AI.

These schemas define the data contract between the HTTP layer and the
GitHubService, making the API self-documenting via FastAPI's OpenAPI output.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ── Input ──────────────────────────────────────────────────────────────────────
class GitHubAnalysisRequest(BaseModel):
    """
    Request body for triggering a GitHub repository analysis.

    The caller supplies the repo URL and an optional date window.
    When *since* / *until* are omitted the service defaults to the last 30 days.
    """

    github_url: HttpUrl = Field(
        ...,
        description="Full URL of the GitHub repository to analyse.",
        examples=["https://github.com/octocat/Hello-World"],
    )
    since: Optional[datetime] = Field(
        default=None,
        description="ISO 8601 timestamp — only commits after this date are included.",
    )
    until: Optional[datetime] = Field(
        default=None,
        description="ISO 8601 timestamp — only commits before this date are included.",
    )
    branch: str = Field(
        default="main",
        description="Branch to analyse.",
        examples=["main", "develop"],
    )

    @field_validator("github_url", mode="before")
    @classmethod
    def validate_github_url(cls, value: str) -> str:
        if "github.com" not in str(value):
            raise ValueError("URL must point to a github.com repository.")
        return value


# ── Intermediate / nested ──────────────────────────────────────────────────────
class AuthorStats(BaseModel):
    """Per-author aggregated statistics within an analysis window."""

    login: str = Field(..., description="GitHub username")
    total_commits: int = Field(..., ge=0)
    total_additions: int = Field(..., ge=0, description="Lines added across all commits")
    total_deletions: int = Field(..., ge=0, description="Lines deleted across all commits")
    first_commit_at: Optional[datetime] = None
    last_commit_at: Optional[datetime] = None


class CommitData(BaseModel):
    """Data for a single Git commit retrieved from the GitHub API."""

    sha: str = Field(..., min_length=7, description="Full or abbreviated commit SHA")
    author_login: Optional[str] = Field(
        default=None,
        description="GitHub username of the commit author (None for unlinked authors)",
    )
    author_name: str = Field(..., description="Git config name of the author")
    author_email: str = Field(..., description="Git config email of the author")
    message: str = Field(..., description="Commit message (first line only)")
    committed_at: datetime = Field(..., description="Timestamp when commit was made")
    additions: int = Field(default=0, ge=0)
    deletions: int = Field(default=0, ge=0)
    files_changed: int = Field(default=0, ge=0)
    url: str = Field(..., description="HTML URL of the commit on GitHub")


# ── Output ─────────────────────────────────────────────────────────────────────
class GitHubAnalysisResponse(BaseModel):
    """
    Full analysis result returned to the client.

    Contains the raw commit list AND pre-computed per-contributor aggregates
    so the frontend has everything it needs without a second request.
    """

    repo_name: str = Field(..., description="owner/repo format", examples=["octocat/Hello-World"])
    repo_url: str = Field(..., description="HTML URL of the analysed repository")
    branch: str = Field(..., description="Branch that was analysed")
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    total_commits: int = Field(..., ge=0)
    commits: List[CommitData] = Field(default_factory=list)
    contributor_stats: Dict[str, AuthorStats] = Field(
        default_factory=dict,
        description="Mapping of GitHub login → aggregated stats",
    )
