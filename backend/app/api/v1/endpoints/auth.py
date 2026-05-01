"""
Auth endpoints — /api/v1/auth

POST /register  → yeni hesap oluştur
POST /login     → JWT token al
GET  /me        → giriş yapan kullanıcının profili
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import RedirectResponse
import httpx

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
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


# ── GitHub OAuth ───────────────────────────────────────────────────────────────
@router.get(
    "/github/login",
    summary="GitHub ile Giriş",
    description="Kullanıcıyı GitHub yetkilendirme sayfasına yönlendirir.",
)
async def github_login():
    import os
    from dotenv import load_dotenv
    
    # 1. Backend klasöründeki .env'yi oku
    load_dotenv(override=True)
    # 2. Üst klasördeki (ana dizindeki) .env'yi de oku (garanti olsun diye)
    load_dotenv("../../.env", override=True)

    # Değişkeni al
    client_id = os.getenv("GITHUB_CLIENT_ID") or settings.GITHUB_CLIENT_ID
    print(f"DEBUG: Yönlendirme için kullanılan GITHUB_CLIENT_ID: '{client_id}'")

    github_auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={client_id}&scope=user:email"
    )
    return RedirectResponse(url=github_auth_url)


@router.get(
    "/github/callback",
    summary="GitHub Callback",
    description="GitHub yetkilendirmesi sonrası kodu alıp Frontend'e token ile yönlendirir.",
)
async def github_callback(
    code: str,
    service: UserService = Depends(get_user_service),
):
    if not code:
        raise HTTPException(status_code=400, detail="Code parametresi bulunamadı.")

    # 1. Exchange code for access token
    import os
    from dotenv import load_dotenv
    load_dotenv(override=True)
    load_dotenv("../../.env", override=True)

    client_id = os.getenv("GITHUB_CLIENT_ID") or settings.GITHUB_CLIENT_ID
    client_secret = os.getenv("GITHUB_CLIENT_SECRET") or settings.GITHUB_CLIENT_SECRET
    frontend_url = os.getenv("FRONTEND_URL") or settings.FRONTEND_URL

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"}
        )
        token_data = token_response.json()
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=f"GitHub yetkilendirme hatası: {token_data.get('error_description')}")
            
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="GitHub access token alınamadı.")

        # 2. Get user profile
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="GitHub profil bilgileri alınamadı.")
            
        user_data = user_response.json()
        github_username = user_data.get("login")
        full_name = user_data.get("name")
        email = user_data.get("email")

        # 3. If email is not public, fetch it explicitly
        if not email:
            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            if emails_response.status_code == 200:
                emails_data = emails_response.json()
                primary_email = next((e["email"] for e in emails_data if e.get("primary")), None)
                if primary_email:
                    email = primary_email
                elif emails_data:
                    email = emails_data[0]["email"]

        if not email or not github_username:
            raise HTTPException(status_code=400, detail="GitHub profili gerekli bilgileri içermiyor (email veya username).")

    # 4. Upsert User using UserService
    user = await service.authenticate_via_github(
        email=email,
        full_name=full_name,
        github_username=github_username
    )

    # 5. Create JWT Token
    jwt_token = create_access_token(subject=str(user.id))
    
    import urllib.parse
    redirect_url = f"{frontend_url}?token={jwt_token}&email={urllib.parse.quote(email)}"
    return RedirectResponse(url=redirect_url)

