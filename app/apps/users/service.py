from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.apps.users.models import User
from app.apps.users.schemas import UserPublicOut, UserPrivateOut, UserUpdateIn


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.db.exec(select(User).where(User.id == user_id))
        return result.first()

    async def _startup_count(self, user_id: str) -> int:
        from sqlmodel import func
        from app.apps.startups.models import Startup
        result = await self.db.exec(
            select(func.count()).where(
                Startup.founder_id == user_id,
                Startup.is_active == True,
            )
        )
        return result.one() or 0

    async def get_public_profile(self, user: User) -> UserPublicOut:
        count = await self._startup_count(user.id)
        return UserPublicOut(
            id=user.id,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            bio=user.bio,
            country=user.country,
            twitter_handle=user.twitter_handle,
            website_url=user.website_url,
            startup_count=count,
            created_at=user.created_at,
        )

    async def get_private_profile(self, user: User) -> UserPrivateOut:
        count = await self._startup_count(user.id)
        return UserPrivateOut(
            id=user.id,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            bio=user.bio,
            country=user.country,
            twitter_handle=user.twitter_handle,
            website_url=user.website_url,
            startup_count=count,
            created_at=user.created_at,
            email=user.email,
            is_verified=user.is_verified,
            primary_provider=user.primary_provider,
        )

    async def update_profile(self, user: User, data: UserUpdateIn) -> UserPrivateOut:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        user.updated_at = datetime.utcnow()
        self.db.add(user)
        return await self.get_private_profile(user)
