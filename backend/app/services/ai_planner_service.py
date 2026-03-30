"""
Service for generating an agile sprint plan using Google Gemini API.
"""
from __future__ import annotations

import json
from enum import Enum
from typing import Dict, List

from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.planner import PlanRequest, PlanResponse


class AiPlannerService:
    def __init__(self) -> None:
        if not hasattr(settings, "GEMINI_API_KEY") or not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing from environment variables.")
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_id = "gemini-2.5-flash"

    async def generate_plan(
        self, request: PlanRequest, member_profiles: Dict[str, str]
    ) -> PlanResponse:
        """
        Generate a structured JSON sprint plan based on the project idea and team profiles.
        """
        profiles_text = "\n\n".join(
            [f"--- Profile for {username} ---\n{profile}" for username, profile in member_profiles.items()]
        )

        prompt = f"""
        You are an expert Agile Scrum Master and Technical Lead.
        Your task is to break down a project into exactly {request.sprint_count} sprints.
        
        PROJECT IDEA:
        {request.project_idea}
        
        TEAM MEMBERS & GITHUB PROFILES:
        {profiles_text}
        
        INSTRUCTIONS & RULES FOR ROLE DISTRIBUTION:
        1. CAPABILITY & SENIORITY MAPPING: First, read every member's GitHub profile. Look at BOTH the areas of experience AND the volume (number of events/commits). 
           - Evaluate "Seniority": Higher event volume in a skill indicates higher seniority.
           - Identify pseudo-fullstacks (Dabblers): If a member has 50 events in Frontend repos and only 2 events in Backend, they are a Frontend Specialist, NOT a Full-stack developer. Do not treat them as a "Joker".
           - Identify "True Generalists" (Jokers) only if they have substantial and somewhat balanced high activity in multiple areas.
        2. BALANCING THE PROJECT: Analyze the PROJECT IDEA and identify its core, most critical technical components.
        3. THE ASSIGNMENT ALGORITHM (STRICT):
           - Phase A (Critical Roles to Seniors): Assign the highest-risk/most critical roles to the members with the highest "Seniority" (highest event volume) in that specific skill.
           - Phase B (The Specialists): Assign the remaining "Pure Specialists" to their distinct skills.
           - Phase C (The Joker Placement): Assign "True Generalists" to the MOST IMPORTANT remaining part of the project, ensuring it is a role they actually have strong, proven experience in.
        4. TIEBREAKER & CONSISTENCY: If members have identical/empty profiles, sort them alphabetically by username and distribute roles deterministically. This prevents random flipping when team sizes change.
        5. SPRINT CONSISTENCY: Once a role is assigned to a person, they MUST keep that EXACT same role in Sprint 1, Sprint 2, etc. Do not swap roles across sprints.
        6. Every task must be assigned to an existing team member from the list.
        7. Define a clear "goal" for each sprint.
        6. Provide the response as a valid JSON object matching exactly this schema:
        {{
            "project_idea": "string",
            "sprint_count": integer,
            "sprints": [
                {{
                    "sprint_number": integer,
                    "goal": "string",
                    "tasks": [
                        {{
                            "title": "string",
                            "description": "string",
                            "assignee": "string",
                            "role_assigned": "string"
                        }}
                    ]
                }}
            ]
        }}
        Do not include markdown code block syntax (like ```json), just the raw JSON object.
        """

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2, # Low temperature for more deterministic role-assignment
            ),
        )

        # Parse JSON and validate with Pydantic
        raw_json = response.text
        data = json.loads(raw_json)
        return PlanResponse(**data)
