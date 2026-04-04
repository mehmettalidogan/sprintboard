"""
Project service for analysis and risk calculation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sprint import Sprint
from app.models.task import Task
from app.schemas.project_analysis import ProjectRiskScore, ProjectTaskAnalysis


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_project_analysis(self, project_id: uuid.UUID) -> ProjectTaskAnalysis:
        """Fetch total task counts separated by status for a project."""
        query = (
            select(Task.status, func.count().label("count"))
            .join(Sprint)
            .where(Sprint.project_id == project_id)
            .group_by(Task.status)
        )
        result = await self.db.execute(query)
        rows = result.all()

        counts = {"completed": 0, "in_progress": 0, "delayed": 0, "pending": 0}
        total = 0
        for status, count in rows:
            clean_status = status.lower().strip()
            if clean_status in counts:
                counts[clean_status] = count
            else:
                counts["pending"] += count
            total += count

        return ProjectTaskAnalysis(
            project_id=project_id,
            total_tasks=total,
            completed_tasks=counts["completed"],
            in_progress_tasks=counts["in_progress"],
            delayed_tasks=counts["delayed"],
            pending_tasks=counts["pending"],
        )

    async def calculate_risk_score(self, project_id: uuid.UUID) -> ProjectRiskScore:
        """
        Calculate risk score using pandas based on deadline urgency, incomplete task ratio, 
        and workload density.
        """
        query = (
            select(Task)
            .join(Sprint)
            .where(Sprint.project_id == project_id)
        )
        result = await self.db.execute(query)
        tasks = result.scalars().all()

        if not tasks:
            return ProjectRiskScore(
                project_id=project_id,
                risk_score=0.0,
                risk_level="Low",
                details={"message": "No tasks found in project sprints."}
            )

        # Build Pandas DataFrame
        data = []
        for t in tasks:
            data.append({
                "id": str(t.id),
                "status": t.status,
                "deadline": t.deadline,
                "assignee_id": str(t.assignee_id) if t.assignee_id else None
            })

        df = pd.DataFrame(data)

        # 1. Incomplete Task Ratio (40% weight)
        total_tasks = len(df)
        completed_df = df[df["status"] == "completed"]
        incomplete_df = df[df["status"] != "completed"]
        
        incomplete_ratio = len(incomplete_df) / total_tasks if total_tasks > 0 else 0.0
        status_risk = incomplete_ratio * 40.0

        # 2. Deadline Urgency (40% weight)
        deadline_risk_score = 0.0
        if not incomplete_df.empty:
            today = datetime.now(tz=timezone.utc).date()
            
            def calculate_urgency(dl):
                if pd.isna(dl) or dl is None:
                    return 0.5  # average risk if no deadline exists
                days_left = (dl - today).days
                if days_left <= 0:
                    return 1.0  # max risk
                elif days_left > 14:
                    return 0.0  # no immediate risk
                else:
                    return (14 - days_left) / 14.0

            urgency_series = incomplete_df["deadline"].apply(calculate_urgency)
            deadline_risk_score = urgency_series.mean() * 40.0

        # 3. Workload Density (20% weight)
        workload_risk_score = 0.0
        if not incomplete_df.empty:
            assigned_df = incomplete_df.dropna(subset=["assignee_id"])
            if not assigned_df.empty:
                # Count incomplete tasks per user
                user_counts = assigned_df.groupby("assignee_id").size()
                max_tasks_for_user = user_counts.max()
                # Consider >= 5 tasks as max risk (100% of the 20 points)
                ratio = min(max_tasks_for_user / 5.0, 1.0)
                workload_risk_score = ratio * 20.0
            else:
                # All incomplete tasks are unassigned
                workload_risk_score = 10.0

        total_risk = min(status_risk + deadline_risk_score + workload_risk_score, 100.0)

        # Determine level
        if total_risk < 30:
            level = "Low"
        elif total_risk < 70:
            level = "Medium"
        else:
            level = "High"

        details = {
            "incomplete_ratio_score": float(status_risk),
            "deadline_risk_score": float(deadline_risk_score),
            "workload_risk_score": float(workload_risk_score),
            "total_tasks": int(total_tasks),
            "incomplete_tasks": int(len(incomplete_df))
        }

        return ProjectRiskScore(
            project_id=project_id,
            risk_score=float(round(total_risk, 2)),
            risk_level=level,
            details=details
        )
