import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException
from app.apps.users.models import User
from app.apps.auth.models import OAuthAccount, RefreshToken
from app.apps.auth.schemas import TokenResponse
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.config import settings


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_or_create_user(
        self,
        provider: str,
        provider_user_id: str,
        email: str,
        full_name: str,
        avatar_url: str | None,
        access_token: str,
        refresh_token: str | None = None,
    ) -> User:
        result = await self.db.exec(
            select(OAuthAccount)
            .where(OAuthAccount.provider == provider)
            .where(OAuthAccount.provider_user_id == str(provider_user_id))
        )
        oauth_account = result.first()

        if oauth_account:
            oauth_account.access_token = access_token
            if refresh_token:
                oauth_account.refresh_token = refresh_token
            oauth_account.updated_at = datetime.utcnow()
            self.db.add(oauth_account)

            result = await self.db.exec(select(User).where(User.id == oauth_account.user_id))
            return result.first()

        result = await self.db.exec(select(User).where(User.email == email))
        user = result.first()

        if not user:
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                full_name=full_name or email.split("@")[0],
                avatar_url=avatar_url,
                primary_provider=provider,
                is_verified=True,
            )
            self.db.add(user)
            await self.db.flush()

        oauth = OAuthAccount(
            id=str(uuid.uuid4()),
            user_id=user.id,
            provider=provider,
            provider_user_id=str(provider_user_id),
            provider_email=email,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        self.db.add(oauth)
        return user

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(user_id=user.id)
        raw_refresh = create_refresh_token(user_id=user.id)

        token_hash = hashlib.sha256(raw_refresh.encode()).hexdigest()
        db_refresh = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(db_refresh)

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def handle_google_callback(self, code: str) -> TokenResponse:
        from app.apps.auth.providers.google import exchange_code_for_token, get_user_info
        token_data = await exchange_code_for_token(code)
        user_info = await get_user_info(token_data["access_token"])
        user = await self._get_or_create_user(
            provider="google",
            provider_user_id=user_info["id"],
            email=user_info["email"],
            full_name=user_info.get("name", ""),
            avatar_url=user_info.get("picture"),
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
        )
        return await self._issue_tokens(user)

    async def handle_github_callback(self, code: str) -> TokenResponse:
        from app.apps.auth.providers.github import exchange_code_for_token, get_user_info
        token_data = await exchange_code_for_token(code)
        user_info = await get_user_info(token_data["access_token"])
        user = await self._get_or_create_user(
            provider="github",
            provider_user_id=user_info["id"],
            email=user_info["email"],
            full_name=user_info.get("name") or user_info.get("login", ""),
            avatar_url=user_info.get("avatar_url"),
            access_token=token_data["access_token"],
        )
        return await self._issue_tokens(user)

    async def refresh(self, raw_refresh_token: str) -> TokenResponse:
        import jwt as pyjwt
        try:
            payload = decode_token(raw_refresh_token)
        except pyjwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        except pyjwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Not a refresh token")

        token_hash = hashlib.sha256(raw_refresh_token.encode()).hexdigest()
        result = await self.db.exec(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .where(RefreshToken.revoked == False)
        )
        db_token = result.first()
        if not db_token:
            raise HTTPException(status_code=401, detail="Refresh token revoked or not found")

        db_token.revoked = True
        self.db.add(db_token)

        result = await self.db.exec(select(User).where(User.id == payload["sub"]))
        user = result.first()
        return await self._issue_tokens(user)

    async def revoke_refresh_token(self, raw_refresh_token: str):
        token_hash = hashlib.sha256(raw_refresh_token.encode()).hexdigest()
        result = await self.db.exec(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        db_token = result.first()
        if db_token:
            db_token.revoked = True
            self.db.add(db_token)
