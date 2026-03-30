"""
SprintBoard AI — FastAPI Application Entry Point

This module creates the FastAPI application instance and wires together:
  - Application lifecycle (startup / shutdown via lifespan context manager)
  - CORS middleware
  - API v1 router
  - Health check endpoint
  - Global exception handling

Run locally with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.core.config import settings
from app.database import engine, get_db
from app.database import Base
import app.models  # noqa: F401 — register all ORM models before create_all
from app.schemas.common import HealthResponse


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Called once on startup and once on shutdown.
    Use this block for:
      - Creating database tables (dev only — use Alembic in production)
      - Warming up connection pools
      - Initialising background task queues
    """
    # ── Startup ────────────────────────────────────────────────────────────────
    async with engine.begin() as conn:
        # NOTE: Replace with `alembic upgrade head` in production deployments
        await conn.run_sync(Base.metadata.create_all)

    print(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} started.")
    yield

    # ── Shutdown ───────────────────────────────────────────────────────────────
    await engine.dispose()
    print("🛑 Database connection pool closed.")


# ── Application factory ────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    """
    Build and configure the FastAPI application.

    Separating construction into a factory function makes the app
    easily testable (override settings before calling create_app()).
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=(
            "SprintBoard AI — GitHub-powered sprint analysis platform.\n\n"
            "Automatically calculates team performance scores and workload balance "
            "using commit history, public holiday calendars, and configurable scoring algorithms."
        ),
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── Middleware ─────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global exception handler ───────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "internal_server_error",
                "details": [{"message": str(exc)}] if settings.DEBUG else [],
            },
        )

    # ── Routes ─────────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["Health"],
        summary="Liveness probe",
        description="Returns 200 OK when the service is running. Used by Docker and load balancers.",
    )
    async def health_check() -> HealthResponse:
        return HealthResponse(status="ok", version=settings.VERSION)

    @app.get(
        "/db-status",
        tags=["Health"],
        summary="Database liveness probe",
        description="Checks if the database is accessible and responsive.",
    )
    async def db_status_check(
        db: AsyncSession = Depends(get_db)  # type: ignore # noqa: F821
    ) -> dict[str, str | bool]:
        try:
            from sqlalchemy import text
            await db.execute(text("SELECT 1"))
            return {"success": True, "message": "Database connection is alive."}
        except Exception as e:
            return {"success": False, "message": f"Database error: {str(e)}"}

    return app


app: FastAPI = create_app()
