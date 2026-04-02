"""
User Pydantic schemas for SprintBoard AI.

Defines the data contracts for user registration, login, and profile responses.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Register ───────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    """Request body for creating a new user account."""

    email: EmailStr = Field(..., description="User's email address", examples=["alice@example.com"])
    password: str = Field(..., min_length=8, description="Plain-text password (min 8 chars)")
    full_name: str | None = Field(default=None, description="Display name", examples=["Alice Smith"])


# ── Login ──────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    """Request body for user login."""

    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Plain-text password")


# ── Token ──────────────────────────────────────────────────────────────────────
class Token(BaseModel):
    """JWT token response returned after successful login or registration."""

    access_token: str
    token_type: str = "bearer"


# ── Profile ────────────────────────────────────────────────────────────────────
class UserResponse(BaseModel):
    """Public user profile — never exposes hashed_password."""

    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Update ─────────────────────────────────────────────────────────────────────
class UserUpdate(BaseModel):
    """Request body for updating existing user details."""

    full_name: str | None = Field(default=None, description="Display name", examples=["Alice Smith"])
    password: str | None = Field(default=None, min_length=8, description="New plain-text password")
