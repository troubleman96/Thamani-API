from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import ok, fail, ApiResponse
from app.apps.saves.service import SavesService
from app.apps.users.models import User

router = APIRouter(prefix="/saves", tags=["Saves"])


@router.post("/{startup_slug}", response_model=ApiResponse[dict])
async def toggle_save(
    startup_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save or unsave a startup. Acts as a toggle."""
    service = SavesService(db)
    result = await service.toggle(user=current_user, startup_slug=startup_slug)
    if result is None:
        return fail("Startup not found")
    action = "saved" if result["saved"] else "unsaved"
    return ok(data=result, message=f"Startup {action} successfully")


@router.get("", response_model=ApiResponse[list])
async def get_my_saves(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all startups saved by the authenticated user."""
    service = SavesService(db)
    items = await service.get_saved(user=current_user)
    return ok(data=items, message="Saved startups retrieved successfully")
