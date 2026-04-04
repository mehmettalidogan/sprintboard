"""
API v1 router — aggregates all v1 endpoint sub-routers.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import auth, github, sprints, planner, projects

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(sprints.router)
api_router.include_router(github.router)
api_router.include_router(planner.router)
api_router.include_router(projects.router)
