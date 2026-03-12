"""
Auth endpoints — /api/v1/auth

POST /register  → yeni hesap oluştur
POST /login     → JWT token al
GET  /me        → giriş yapan kullanıcının profili
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, DbSession
from app.core.security import create_access_token
from app.schemas.user import LoginRequest, Token, UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_user_service(db: DbSession) -> UserService:
    return UserService(db)


# ── Register ───────────────────────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni kullanıcı kaydı",
    description="E-posta ve şifre ile yeni hesap oluşturur, hemen JWT token döner.",
)
async def register(
    body: UserCreate,
    service: UserService = Depends(get_user_service),
) -> Token:
    user = await service.register(body)
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


# ── Login ──────────────────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Giriş yap",
    description="E-posta ve şifre doğrulanırsa JWT access token döner.",
)
async def login(
    body: LoginRequest,
    service: UserService = Depends(get_user_service),
) -> Token:
    user = await service.authenticate(body.email, body.password)
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


# ── Me ─────────────────────────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Profil bilgisi",
    description="Authorization header'daki JWT token'dan kullanıcı profilini döner.",
)
async def get_me(
    current_user_id: CurrentUser,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.get_by_id(current_user_id)
    return UserResponse.model_validate(user)
