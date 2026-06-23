from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import ok, fail, ApiResponse
from app.apps.verification.schemas import ConnectProviderIn, VerificationStatusOut
from app.apps.verification.service import VerificationService
from app.apps.users.models import User

router = APIRouter(prefix="/verification", tags=["Verification"])


@router.post("/{startup_slug}/connect", response_model=ApiResponse[VerificationStatusOut])
async def connect_provider(
    startup_slug: str,
    body: ConnectProviderIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Connect a payment provider to a startup. Credentials are AES-256 encrypted.
    Immediately tests credentials and marks startup as verified on success.
    """
    service = VerificationService(db)
    result = await service.connect_provider(
        startup_slug=startup_slug,
        founder=current_user,
        data=body,
    )
    if not result:
        return fail("Startup not found or not yours")
    return ok(data=result, message=f"{body.provider} connected successfully")


@router.post("/{startup_slug}/sync", response_model=ApiResponse[VerificationStatusOut])
async def sync_revenue(
    startup_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a revenue sync from the connected provider."""
    service = VerificationService(db)
    result = await service.trigger_sync(startup_slug=startup_slug, founder=current_user)
    return ok(data=result, message="Revenue sync triggered successfully")


@router.get("/{startup_slug}/status", response_model=ApiResponse[VerificationStatusOut])
async def get_verification_status(
    startup_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VerificationService(db)
    result = await service.get_status(startup_slug=startup_slug, founder=current_user)
    if not result:
        return fail("No verification credentials found")
    return ok(data=result, message="Verification status retrieved")
