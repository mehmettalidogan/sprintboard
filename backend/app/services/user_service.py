"""
UserService — User registration and authentication logic.

Single responsibility: all database operations related to users live here.
Route handlers depend on this service via FastAPI Depends.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate


class UserService:

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Register ───────────────────────────────────────────────────────────────
    async def register(self, data: UserCreate) -> User:
        """
        Create a new user account.

        Raises:
            HTTPException 409: If the email is already registered.
        """
        existing = await self._get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bu e-posta adresi zaten kayıtlı.",
            )

        user = User(
            email=data.email.lower().strip(),
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )
        self._db.add(user)
        await self._db.flush()   # ID'yi almak için flush, commit session tarafından yapılır
        await self._db.refresh(user)
        return user

    # ── Authenticate ───────────────────────────────────────────────────────────
    async def authenticate(self, email: str, password: str) -> User:
        """
        Verify email + password and return the user.

        Raises:
            HTTPException 401: If credentials are invalid or user is inactive.
        """
        invalid_credentials = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı.",
            headers={"WWW-Authenticate": "Bearer"},
        )

        user = await self._get_by_email(email)
        if not user:
            raise invalid_credentials
        if not verify_password(password, user.hashed_password):
            raise invalid_credentials
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu hesap devre dışı bırakılmış.",
            )
        return user

    # ── Authenticate via GitHub ────────────────────────────────────────────────
    async def authenticate_via_github(self, email: str, full_name: str | None, github_username: str) -> User:
        """
        Authenticate or register a user via GitHub OAuth (Upsert logic).
        """
        import secrets
        import string

        # 1. Check if user exists with this github_username
        result = await self._db.execute(
            select(User).where(User.github_username == github_username)
        )
        user = result.scalar_one_or_none()

        if user:
            # Login (Eski Kullanıcı)
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu hesap devre dışı bırakılmış.",
                )
            return user

        # 2. Check if email exists (to avoid IntegrityError if they registered via email earlier)
        existing_email_user = await self._get_by_email(email)
        if existing_email_user:
            # Link GitHub profile to existing account
            existing_email_user.github_username = github_username
            if full_name and not existing_email_user.full_name:
                existing_email_user.full_name = full_name
            await self._db.flush()
            await self._db.refresh(existing_email_user)
            return existing_email_user

        # 3. Create (Yeni Kullanıcı)
        # Generate a random secure password since hashed_password is required
        alphabet = string.ascii_letters + string.digits + string.punctuation
        random_password = ''.join(secrets.choice(alphabet) for i in range(16))

        user = User(
            email=email.lower().strip(),
            full_name=full_name,
            github_username=github_username,
            hashed_password=hash_password(random_password),
        )
        self._db.add(user)
        await self._db.flush()   # ID'yi almak için flush, commit session tarafından yapılır
        await self._db.refresh(user)
        return user

    # ── Get by ID ──────────────────────────────────────────────────────────────
    async def get_by_id(self, user_id: str) -> User:
        """
        Fetch a user by their UUID string.

        Raises:
            HTTPException 404: If the user does not exist.
        """
        result = await self._db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kullanıcı bulunamadı.",
            )
        return user

    # ── Private helpers ────────────────────────────────────────────────────────
    async def _get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()
