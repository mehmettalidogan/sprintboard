"""
Analytics Service — Synthesizes GitHub, NLP, and Time metrics using Pandas.
"""
from __future__ import annotations

import uuid
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.models.task import Task
from app.models.user import User
from app.schemas.analytics import MemberProductivityOut, SprintProductivityReport
from app.services.github_mock_service import GitHubMockService
from app.services.nlp_mock_service import NLPMockService

MAX_EXPECTED_GITHUB_ACTIVITY = 20

class AnalyticsService:
    def __init__(
        self,
        github_mock_service: GitHubMockService,
        nlp_mock_service: NLPMockService,
    ) -> None:
        self.github_mock = github_mock_service
        self.nlp_mock = nlp_mock_service

    async def calculate_member_productivity(
        self, sprint_id: uuid.UUID, db: AsyncSession
    ) -> SprintProductivityReport:
        # 1. Fetch all tasks for the given sprint
        result = await db.execute(select(Task).where(Task.sprint_id == sprint_id))
        tasks = result.scalars().all()
        
        # We need a list of assignees for these tasks
        assignee_ids = list(set([t.assignee_id for t in tasks if t.assignee_id is not None]))
        
        if not assignee_ids:
            return SprintProductivityReport(
                sprint_id=sprint_id,
                total_members_analyzed=0,
                member_reports=[]
            )

        # 2. Fetch users
        users_result = await db.execute(select(User).where(User.id.in_(assignee_ids)))
        users = {u.id: u for u in users_result.scalars().all()}

        # Construct DataFrame
        task_data = []
        for t in tasks:
            if not t.assignee_id:
                continue
                
            # A task is successfully on time if status is completed and updated_at <= deadline
            # If deadline is null/NaN, we consider it finished on time if it is completed.
            is_completed = (t.status == "completed")
            is_on_time = False
            
            if is_completed:
                if pd.isna(t.deadline) or t.deadline is None:
                    is_on_time = True
                elif t.updated_at.date() <= t.deadline:
                    is_on_time = True
                    
            task_data.append({
                "task_id": str(t.id),
                "assignee_id": str(t.assignee_id),
                "status": t.status,
                "is_completed": is_completed,
                "is_on_time": is_on_time,
                "nlp_complexity_score": t.nlp_complexity_score
            })
            
        df = pd.DataFrame(task_data)
        
        if df.empty:
            return SprintProductivityReport(
                sprint_id=sprint_id,
                total_members_analyzed=0,
                member_reports=[]
            )

        member_reports: List[MemberProductivityOut] = []

        # Iterate per member
        for uid in assignee_ids:
            str_uid = str(uid)
            user = users.get(uid)
            if not user:
                continue

            member_df = df[df['assignee_id'] == str_uid]
            if member_df.empty:
                continue

            # --- Time/Risk Success (40%) ---
            total_member_tasks = len(member_df)
            on_time_tasks = member_df['is_on_time'].sum()
            # Safety fillna inside pandas logic, though here it's simple division
            time_success_ratio = on_time_tasks / total_member_tasks if total_member_tasks > 0 else 0
            time_risk_score = time_success_ratio * 100.0

            # --- Task Difficulty / NLP Coefficient (30%) ---
            completed_df = member_df[member_df['is_completed'] == True]
            if not completed_df.empty:
                avg_complexity = completed_df['nlp_complexity_score'].mean()
            else:
                avg_complexity = 0.0
                
            # Normalize NLP score (1-5 range to 0-100 range)
            # fillna with 0 for safety
            if pd.isna(avg_complexity):
                avg_complexity = 0.0

            if avg_complexity > 0:
                nlp_normalized = ((avg_complexity - 1) / 4.0) * 100.0
            else:
                nlp_normalized = 0.0
            
            nlp_normalized = pd.Series([nlp_normalized]).fillna(0).iloc[0]
            
            # --- Technical Effort / GitHub Coefficient (30%) ---
            gh_stats = await self.github_mock.get_mock_developer_stats(
                github_username=user.github_username or user.email,
                start_date=pd.to_datetime("today").date(),
                end_date=pd.to_datetime("today").date()
            )
            total_effort = gh_stats["total_effort"] # commits + prs
            
            gh_ratio = total_effort / MAX_EXPECTED_GITHUB_ACTIVITY
            github_effort_score = min(gh_ratio * 100.0, 100.0)

            # --- Final Synthesis ---
            final_productivity_score = (
                (time_risk_score * 0.40) + 
                (nlp_normalized * 0.30) + 
                (github_effort_score * 0.30)
            )

            member_reports.append(
                MemberProductivityOut(
                    user_id=uid,
                    email=user.email,
                    github_username=user.github_username,
                    time_risk_score=round(time_risk_score, 2),
                    nlp_complexity_score=round(nlp_normalized, 2),
                    github_effort_score=round(github_effort_score, 2),
                    final_productivity_score=round(final_productivity_score, 2)
                )
            )

        return SprintProductivityReport(
            sprint_id=sprint_id,
            total_members_analyzed=len(member_reports),
            member_reports=member_reports
        )
