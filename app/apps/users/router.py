from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import ok, fail, ApiResponse
from app.apps.users.schemas import UserPublicOut, UserPrivateOut, UserUpdateIn
from app.apps.users.service import UserService
from app.apps.users.models import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=ApiResponse[UserPrivateOut])
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    data = await service.get_private_profile(current_user)
    return ok(data=data, message="Profile retrieved successfully")


@router.patch("/me", response_model=ApiResponse[UserPrivateOut])
async def update_my_profile(
    body: UserUpdateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    data = await service.update_profile(current_user, body)
    return ok(data=data, message="Profile updated successfully")


@router.get("/{user_id}", response_model=ApiResponse[UserPublicOut])
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    user = await service.get_by_id(user_id)
    if not user:
        return fail("User not found", errors=[f"No user with id '{user_id}'"])
    data = await service.get_public_profile(user)
    return ok(data=data, message="User retrieved successfully")
