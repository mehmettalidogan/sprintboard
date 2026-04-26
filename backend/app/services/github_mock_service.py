"""
Mock GitHub Service — simulates fetching commit, PR, and additions/deletions data.
"""
from __future__ import annotations

import random
from datetime import date
from typing import Dict, Any

class GitHubMockService:
    """
    Mock service to generate random GitHub stats for a developer
    in a given date range.
    """

    async def get_mock_developer_stats(
        self, github_username: str, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """
        Returns mock stats: commits, prs, additions, deletions.
        """
        # Generate some random activity
        commits = random.randint(5, 30)
        prs = random.randint(1, 10)
        additions = random.randint(100, 5000)
        deletions = random.randint(50, 2500)
        
        return {
            "github_username": github_username,
            "commits": commits,
            "prs": prs,
            "additions": additions,
            "deletions": deletions,
            "total_effort": commits + prs  # Example metric
        }
