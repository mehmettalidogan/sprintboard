"""
Common / shared Pydantic response schemas.

Keep generic building blocks here so they can be reused across all
feature-specific schema modules without circular imports.
"""

from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


# ── Health ─────────────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    """Response body for the /health liveness probe endpoint."""

    status: str = Field(default="ok", examples=["ok"])
    version: str = Field(..., examples=["0.1.0"])


# ── Standard error ─────────────────────────────────────────────────────────────
class ErrorDetail(BaseModel):
    """Single validation or domain error."""

    field: str | None = Field(default=None, examples=["github_url"])
    message: str = Field(..., examples=["Invalid GitHub repository URL format."])


class ErrorResponse(BaseModel):
    """Standard error envelope returned on 4xx / 5xx responses."""

    success: bool = Field(default=False)
    error: str = Field(..., examples=["validation_error"])
    details: List[ErrorDetail] = Field(default_factory=list)


# ── Paginated response ─────────────────────────────────────────────────────────
class PaginatedResponse(BaseModel, Generic[DataT]):
    """
    Generic paginated list response.

    Usage:
        PaginatedResponse[CommitData](items=[...], total=42, page=1, size=20)
    """

    items: List[DataT]
    total: int = Field(..., ge=0, description="Total number of matching records")
    page: int = Field(default=1, ge=1, description="Current page number (1-indexed)")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")
    has_next: bool = Field(default=False)

    @classmethod
    def from_items(
        cls,
        items: List[DataT],
        total: int,
        page: int,
        size: int,
    ) -> "PaginatedResponse[DataT]":
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            has_next=(page * size) < total,
        )
