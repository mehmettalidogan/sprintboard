"""
Central configuration module for SprintBoard AI.

Reads all settings from environment variables / .env file using pydantic-settings.
Single source of truth for every secret and configuration value in the project.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    PROJECT_NAME: str = Field(default="SprintBoard AI", description="Human-readable app name")
    VERSION: str = Field(default="0.1.0", description="Semantic version of the API")
    DEBUG: bool = Field(default=False, description="Enable debug mode (never True in prod)")
    API_V1_STR: str = Field(default="/api/v1", description="API version prefix")

    # ── Security ───────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(..., description="Secret key used for JWT signing")
    ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24,  # 24 hours
        description="JWT token expiration time in minutes",
    )

    # ── Database ───────────────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        ...,
        description=(
            "Async PostgreSQL connection string. "
            "Example: postgresql+asyncpg://user:pass@localhost:5432/sprintboard"
        ),
    )

    # ── GitHub API ─────────────────────────────────────────────────────────────
    GITHUB_TOKEN: str = Field(..., description="GitHub Personal Access Token (PAT)")
    GITHUB_API_BASE_URL: AnyHttpUrl = Field(
        default="https://api.github.com",
        description="Base URL for GitHub REST API",
    )
    GITHUB_PER_PAGE: int = Field(
        default=100,
        ge=1,
        le=100,
        description="Number of results per page for GitHub API (max 100)",
    )

    # -- AI Planner Integrations --
    GEMINI_API_KEY: str = Field(..., description="API Key for Google Gemini LLM")

    # ── Public Holiday API ─────────────────────────────────────────────────────
    HOLIDAY_API_BASE_URL: AnyHttpUrl = Field(
        default="https://date.nager.at/api/v3",
        description="Base URL for the Nager.Date Public Holiday API (free, no key needed)",
    )
    HOLIDAY_API_KEY: str | None = Field(
        default=None,
        description="Optional API key if using a paid holiday data provider",
    )
    DEFAULT_COUNTRY_CODE: str = Field(
        default="TR",
        description="ISO 3166-1 alpha-2 country code used as default for holiday lookups",
    )

    # ── CORS ───────────────────────────────────────────────────────────────────
    BACKEND_CORS_ORIGINS: str | List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="List of allowed CORS origins for the frontend",
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: str | List[str]) -> str | List[str]:
        """Allow BACKEND_CORS_ORIGINS to be supplied as a comma-separated string."""
        if isinstance(value, str) and not value.startswith("["):
            return [origin.strip() for origin in value.split(",")]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return cached Settings instance.

    Using @lru_cache ensures the .env file is parsed only once per process,
    while still allowing tests to override by calling get_settings.cache_clear().
    """
    return Settings()


# Convenience alias — use `settings.GITHUB_TOKEN` anywhere in the codebase
settings: Settings = get_settings()
