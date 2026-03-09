"""
GitHubService — Async client for the GitHub REST API.

Responsibilities (Single Responsibility Principle):
  - Fetch commit history for a repository and date range
  - Retrieve contributor statistics
  - Parse and map raw API responses to domain schemas

All network I/O is non-blocking via httpx.AsyncClient.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import settings
from app.schemas.github import AuthorStats, CommitData, GitHubAnalysisResponse


class GitHubServiceError(Exception):
    """Raised when the GitHub API returns an unexpected response."""


class GitHubService:
    """
    Async wrapper around the GitHub REST API v3.

    Designed to be used as an async context manager inside FastAPI
    dependency injection so the underlying httpx client is properly
    closed after each request lifecycle.

    Usage (inside a route handler)::

        async with GitHubService() as svc:
            commits = await svc.get_commits(repo_url="https://github.com/org/repo")
    """

    _COMMIT_PATH = "/repos/{owner}/{repo}/commits"
    _STATS_PATH = "/repos/{owner}/{repo}/stats/contributors"

    def __init__(self) -> None:
        self._base_url = str(settings.GITHUB_API_BASE_URL).rstrip("/")
        self._headers: Dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        }
        self._client: httpx.AsyncClient | None = None

    # ── Context manager ────────────────────────────────────────────────────────
    async def __aenter__(self) -> "GitHubService":
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._headers,
            timeout=httpx.Timeout(30.0),
        )
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ── Public API ─────────────────────────────────────────────────────────────
    async def get_commits(
        self,
        repo_url: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        branch: str = "main",
    ) -> List[CommitData]:
        """
        Fetch the commit history for a GitHub repository.

        Args:
            repo_url: Full GitHub repository URL.
            since:    Inclusive start of the time window (UTC).
                      Defaults to 30 days ago.
            until:    Inclusive end of the time window (UTC).
                      Defaults to now.
            branch:   Branch / ref to fetch commits from.

        Returns:
            List of :class:`CommitData` objects ordered by most recent first.

        Raises:
            GitHubServiceError: On HTTP errors or unexpected response shapes.
        """
        self._ensure_client()
        owner, repo = self._parse_repo_url(repo_url)

        since = since or datetime.now(tz=timezone.utc) - timedelta(days=30)
        until = until or datetime.now(tz=timezone.utc)

        commits: List[CommitData] = []
        page = 1

        while True:
            params: Dict[str, Any] = {
                "sha": branch,
                "since": since.isoformat(),
                "until": until.isoformat(),
                "per_page": settings.GITHUB_PER_PAGE,
                "page": page,
            }
            response = await self._client.get(  # type: ignore[union-attr]
                self._COMMIT_PATH.format(owner=owner, repo=repo),
                params=params,
            )
            self._raise_for_status(response)

            page_data: List[Dict[str, Any]] = response.json()
            if not page_data:
                break

            for raw in page_data:
                commits.append(self._map_commit(raw))

            # GitHub paginates via Link header — stop when fewer than a full page
            if len(page_data) < settings.GITHUB_PER_PAGE:
                break
            page += 1

        return commits

    async def get_contributors(
        self,
        repo_url: str,
    ) -> Dict[str, AuthorStats]:
        """
        Fetch aggregated contributor statistics from GitHub.

        GitHub computes these stats asynchronously; a 202 response means
        the data is not ready yet.  We retry up to 3 times in that case.

        Returns:
            Dict mapping GitHub login → :class:`AuthorStats`.
        """
        self._ensure_client()
        owner, repo = self._parse_repo_url(repo_url)

        for _ in range(3):
            response = await self._client.get(  # type: ignore[union-attr]
                self._STATS_PATH.format(owner=owner, repo=repo),
            )
            if response.status_code == 202:
                # Stats are being computed — short sleep then retry
                import asyncio
                await asyncio.sleep(2)
                continue
            self._raise_for_status(response)
            return self._map_contributor_stats(response.json())

        raise GitHubServiceError(
            "GitHub contributor stats are still being computed. Please retry shortly."
        )

    async def get_analysis(
        self,
        repo_url: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        branch: str = "main",
    ) -> GitHubAnalysisResponse:
        """
        Convenience method that fetches commits and returns a full analysis DTO.

        Aggregates commit data into per-author stats inline so the service
        layer does not need to call get_commits and get_contributors separately.
        """
        owner, repo = self._parse_repo_url(repo_url)
        commits = await self.get_commits(repo_url, since, until, branch)
        contributor_stats = self._aggregate_stats(commits)

        return GitHubAnalysisResponse(
            repo_name=f"{owner}/{repo}",
            repo_url=repo_url,
            branch=branch,
            since=since,
            until=until,
            total_commits=len(commits),
            commits=commits,
            contributor_stats=contributor_stats,
        )

    # ── Private helpers ────────────────────────────────────────────────────────
    def _ensure_client(self) -> None:
        if self._client is None:
            raise RuntimeError(
                "GitHubService must be used as an async context manager. "
                "Use `async with GitHubService() as svc:`"
            )

    @staticmethod
    def _parse_repo_url(url: str) -> Tuple[str, str]:
        """
        Extract (owner, repo) from a GitHub URL.

        Handles:
          - https://github.com/owner/repo
          - https://github.com/owner/repo.git
          - https://github.com/owner/repo/tree/branch
        """
        pattern = r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)"
        match = re.search(pattern, str(url))
        if not match:
            raise GitHubServiceError(
                f"Cannot parse owner/repo from URL: {url!r}. "
                "Expected format: https://github.com/owner/repo"
            )
        return match.group("owner"), match.group("repo")

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        """Raise :class:`GitHubServiceError` with a descriptive message on errors."""
        if response.is_error:
            try:
                message = response.json().get("message", response.text)
            except Exception:
                message = response.text
            raise GitHubServiceError(
                f"GitHub API error {response.status_code}: {message}"
            )

    @staticmethod
    def _map_commit(raw: Dict[str, Any]) -> CommitData:
        """Map a raw GitHub API commit object to a :class:`CommitData`."""
        commit_detail = raw.get("commit", {})
        author_detail = commit_detail.get("author", {})
        github_author = raw.get("author") or {}
        stats = raw.get("stats", {})

        return CommitData(
            sha=raw.get("sha", "")[:40],
            author_login=github_author.get("login"),
            author_name=author_detail.get("name", "Unknown"),
            author_email=author_detail.get("email", ""),
            message=(commit_detail.get("message", "") or "").split("\n")[0][:256],
            committed_at=datetime.fromisoformat(
                author_detail.get("date", datetime.now(tz=timezone.utc).isoformat())
            ),
            additions=stats.get("additions", 0),
            deletions=stats.get("deletions", 0),
            files_changed=len(raw.get("files", [])),
            url=raw.get("html_url", ""),
        )

    @staticmethod
    def _map_contributor_stats(data: List[Dict[str, Any]]) -> Dict[str, AuthorStats]:
        """Map raw contributor stats from GitHub to :class:`AuthorStats` objects."""
        result: Dict[str, AuthorStats] = {}
        for entry in data:
            author = entry.get("author") or {}
            login = author.get("login", "unknown")
            weeks = entry.get("weeks", [])
            result[login] = AuthorStats(
                login=login,
                total_commits=entry.get("total", 0),
                total_additions=sum(w.get("a", 0) for w in weeks),
                total_deletions=sum(w.get("d", 0) for w in weeks),
            )
        return result

    @staticmethod
    def _aggregate_stats(commits: List[CommitData]) -> Dict[str, AuthorStats]:
        """Compute per-author stats from a flat list of CommitData objects."""
        agg: Dict[str, Dict[str, Any]] = {}
        for c in commits:
            login = c.author_login or c.author_name
            if login not in agg:
                agg[login] = {
                    "login": login,
                    "total_commits": 0,
                    "total_additions": 0,
                    "total_deletions": 0,
                    "first_commit_at": c.committed_at,
                    "last_commit_at": c.committed_at,
                }
            entry = agg[login]
            entry["total_commits"] += 1
            entry["total_additions"] += c.additions
            entry["total_deletions"] += c.deletions
            if c.committed_at < entry["first_commit_at"]:
                entry["first_commit_at"] = c.committed_at
            if c.committed_at > entry["last_commit_at"]:
                entry["last_commit_at"] = c.committed_at

        return {login: AuthorStats(**data) for login, data in agg.items()}
