import secrets
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.core.response import ok, ApiResponse
from app.core.dependencies import get_current_user
from app.apps.auth.schemas import TokenResponse, RefreshRequest, AuthUserOut
from app.apps.auth.service import AuthService
from app.apps.users.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/google/login")
async def google_login():
    from app.apps.auth.providers.google import get_google_auth_url
    state = secrets.token_urlsafe(32)
    return RedirectResponse(url=get_google_auth_url(state=state))


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        result = await service.handle_google_callback(code=code)
        redirect_url = (
            f"{settings.FRONTEND_URL}/auth/callback"
            f"?access_token={result.access_token}"
            f"&refresh_token={result.refresh_token}"
        )
        return RedirectResponse(url=redirect_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/github/login")
async def github_login():
    from app.apps.auth.providers.github import get_github_auth_url
    state = secrets.token_urlsafe(32)
    return RedirectResponse(url=get_github_auth_url(state=state))


@router.get("/github/callback")
async def github_callback(
    code: str,
    state: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        result = await service.handle_github_callback(code=code)
        redirect_url = (
            f"{settings.FRONTEND_URL}/auth/callback"
            f"?access_token={result.access_token}"
            f"&refresh_token={result.refresh_token}"
        )
        return RedirectResponse(url=redirect_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    result = await service.refresh(body.refresh_token)
    return ok(data=result, message="Token refreshed successfully")


@router.post("/logout", response_model=ApiResponse[None])
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.revoke_refresh_token(body.refresh_token)
    return ok(message="Logged out successfully")


@router.get("/me", response_model=ApiResponse[AuthUserOut])
async def get_me(current_user: User = Depends(get_current_user)):
    return ok(
        data=AuthUserOut(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            avatar_url=current_user.avatar_url,
            provider=current_user.primary_provider,
            is_verified=current_user.is_verified,
        ),
        message="User retrieved successfully",
    )
