"""
AnalysisService — Sprint performance and workload balance engine.

Orchestrates GitHubService and HolidayService to produce the final
performance and workload-balance scores for a sprint.

Design notes
------------
* Open/Closed:  New scoring algorithms can be added without modifying
  existing ones — scoring is handled by small private helper methods.
* Dependency Inversion:  Services are injected via the constructor,
  making the class easily testable with mocks.
"""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from app.schemas.github import CommitData
from app.schemas.sprint import MemberPerformance, SprintCreate, SprintResponse
from app.services.github_service import GitHubService
from app.services.holiday_service import HolidayService

import uuid


class AnalysisService:
    """
    Coordinates the full sprint analysis pipeline.

    Usage::

        async with GitHubService() as gh, HolidayService() as hol:
            svc = AnalysisService(gh, hol)
            result = await svc.analyse_sprint(sprint_input)
    """

    def __init__(
        self,
        github_service: GitHubService,
        holiday_service: HolidayService,
    ) -> None:
        self._github = github_service
        self._holiday = holiday_service

    # ── Public API ─────────────────────────────────────────────────────────────
    async def analyse_sprint(self, sprint: SprintCreate) -> SprintResponse:
        """
        Run the full analysis pipeline for a sprint and return results.

        Pipeline steps:
          1. Fetch GitHub commits for the sprint date window.
          2. Count working days (excluding public holidays and weekends).
          3. Compute per-member performance breakdowns.
          4. Calculate aggregate workload-balance and performance scores.

        Args:
            sprint: Validated :class:`SprintCreate` payload from the request.

        Returns:
            :class:`SprintResponse` populated with computed scores.
        """
        repo_url = str(sprint.github_url)

        # ── Step 1: Fetch commits ──────────────────────────────────────────────
        since_dt = _date_to_datetime(sprint.start_date)
        until_dt = _date_to_datetime(sprint.end_date, end_of_day=True)
        commits = await self._github.get_commits(repo_url, since_dt, until_dt)

        # ── Step 2: Count working days ─────────────────────────────────────────
        total_working_days = await self._holiday.count_working_days(
            start=sprint.start_date,
            end=sprint.end_date,
            country_code=sprint.country_code,
        )

        # ── Step 3: Per-member breakdown ───────────────────────────────────────
        team = [m.lower() for m in sprint.team_members]
        member_stats = self._aggregate_member_stats(commits, team)
        total_commits = sum(s["total_commits"] for s in member_stats.values())

        member_performance: List[MemberPerformance] = []
        for login, stats in member_stats.items():
            share = stats["total_commits"] / total_commits if total_commits else 0.0
            member_performance.append(
                MemberPerformance(
                    github_login=login,
                    total_commits=stats["total_commits"],
                    total_additions=stats["total_additions"],
                    total_deletions=stats["total_deletions"],
                    active_days=stats["active_days"],
                    workload_share=round(share, 4),
                )
            )

        # ── Step 4: Compute scores ─────────────────────────────────────────────
        workload_balance = self.calculate_workload_balance(member_performance)
        performance = self.calculate_performance_score(
            commits=commits,
            total_working_days=total_working_days,
            sprint=sprint,
        )

        notes = self._generate_notes(
            commits=commits,
            total_working_days=total_working_days,
            workload_balance=workload_balance,
            performance=performance,
        )

        from datetime import datetime, timezone
        now = datetime.now(tz=timezone.utc)

        return SprintResponse(
            id=uuid.uuid4(),
            github_url=repo_url,
            start_date=sprint.start_date,
            end_date=sprint.end_date,
            team_members=sprint.team_members,
            country_code=sprint.country_code,
            status="completed",
            performance_score=round(performance, 2),
            workload_balance_score=round(workload_balance, 2),
            total_working_days=total_working_days,
            analysis_notes=notes,
            member_performance=member_performance,
            created_at=now,
            updated_at=now,
        )

    # ── Scoring algorithms ─────────────────────────────────────────────────────
    @staticmethod
    def calculate_workload_balance(
        members: List[MemberPerformance],
    ) -> float:
        """
        Calculate a workload balance score (0–100).

        Uses the Gini coefficient of commit counts to measure inequality.
        A Gini of 0 means perfect equality (score = 100);
        a Gini of 1 means total inequality (score = 0).

        Returns:
            Float in [0, 100] — higher is more balanced.
        """
        if not members:
            return 0.0

        shares = sorted(m.workload_share for m in members)
        n = len(shares)
        if n == 1:
            return 100.0  # Only one contributor — trivially balanced

        # Gini coefficient via sorted-array formula
        numerator = sum((2 * (i + 1) - n - 1) * s for i, s in enumerate(shares))
        gini = numerator / (n * sum(shares)) if sum(shares) > 0 else 0.0
        return round(max(0.0, (1.0 - gini)) * 100, 2)

    @staticmethod
    def calculate_performance_score(
        commits: List[CommitData],
        total_working_days: int,
        sprint: SprintCreate,
    ) -> float:
        """
        Calculate a normalised sprint performance score (0–100).

        Formula considers:
          - Commit velocity (commits per working day vs team expectation)
          - Code churn ratio (additions vs deletions balance)
          - Consistency (were commits spread across working days?)

        Returns:
            Float in [0, 100] — higher is better.
        """
        if not commits or total_working_days == 0:
            return 0.0

        team_size = max(len(sprint.team_members), 1)
        expected_commits_per_day = team_size * 2   # baseline: 2 commits/dev/day
        expected_total = expected_commits_per_day * total_working_days

        # ── Velocity score (0-50 weight) ──────────────────────────────────────
        actual_total = len(commits)
        velocity_ratio = min(actual_total / expected_total, 2.0)  # cap at 2x
        velocity_score = min(velocity_ratio * 50, 50.0)

        # ── Consistency score (0-30 weight) ───────────────────────────────────
        active_days = len({c.committed_at.date() for c in commits})
        consistency_ratio = active_days / total_working_days
        consistency_score = consistency_ratio * 30

        # ── Churn ratio score (0-20 weight) ───────────────────────────────────
        total_additions = sum(c.additions for c in commits)
        total_deletions = sum(c.deletions for c in commits)
        total_changes = total_additions + total_deletions
        # A healthy ratio has more additions than deletions; penalise heavy churn
        if total_changes > 0:
            churn_ratio = total_additions / total_changes
            churn_score = churn_ratio * 20
        else:
            churn_score = 10.0  # neutral when no diff data available

        return min(velocity_score + consistency_score + churn_score, 100.0)

    # ── Private helpers ────────────────────────────────────────────────────────
    @staticmethod
    def _aggregate_member_stats(
        commits: List[CommitData],
        team_logins: List[str],
    ) -> Dict[str, Dict]:
        """Group commits by author and compute per-member raw stats."""
        agg: Dict[str, Dict] = {
            login: {
                "total_commits": 0,
                "total_additions": 0,
                "total_deletions": 0,
                "active_dates": set(),
            }
            for login in team_logins
        }
        # Also bucket untracked authors under their login
        for c in commits:
            login = (c.author_login or c.author_name).lower()
            if login not in agg:
                agg[login] = {
                    "total_commits": 0,
                    "total_additions": 0,
                    "total_deletions": 0,
                    "active_dates": set(),
                }
            agg[login]["total_commits"] += 1
            agg[login]["total_additions"] += c.additions
            agg[login]["total_deletions"] += c.deletions
            agg[login]["active_dates"].add(c.committed_at.date())

        # Resolve set → count for serialisation
        return {
            login: {**data, "active_days": len(data["active_dates"])}
            for login, data in agg.items()
            if data["total_commits"] > 0
        }

    @staticmethod
    def _generate_notes(
        commits: List[CommitData],
        total_working_days: int,
        workload_balance: float,
        performance: float,
    ) -> str:
        """Generate a human-readable summary of the analysis results."""
        lines = [
            f"Analysed {len(commits)} commit(s) across {total_working_days} working day(s).",
        ]
        if workload_balance >= 80:
            lines.append("✅ Team workload is well-balanced.")
        elif workload_balance >= 50:
            lines.append("⚠️  Some workload imbalance detected — consider redistributing tasks.")
        else:
            lines.append("🚨 Significant workload imbalance — one or more members are overloaded.")

        if performance >= 75:
            lines.append("✅ Sprint velocity is on track.")
        elif performance >= 40:
            lines.append("⚠️  Sprint velocity is below expectation.")
        else:
            lines.append("🚨 Sprint velocity is critically low.")

        return " ".join(lines)


# ── Utility ────────────────────────────────────────────────────────────────────
def _date_to_datetime(d: date, end_of_day: bool = False):
    """Convert a naive date to a timezone-aware datetime (UTC)."""
    from datetime import datetime, time, timezone
    t = time(23, 59, 59) if end_of_day else time(0, 0, 0)
    return datetime.combine(d, t, tzinfo=timezone.utc)
