import uuid
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.apps.saves.models import SavedStartup
from app.apps.startups.models import Startup
from app.apps.users.models import User


class SavesService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def toggle(self, user: User, startup_slug: str) -> dict:
        """Save or unsave a startup. Returns current saved state."""
        result = await self.db.exec(
            select(Startup).where(Startup.slug == startup_slug, Startup.is_active == True)
        )
        startup = result.first()
        if not startup:
            return None

        result = await self.db.exec(
            select(SavedStartup).where(
                SavedStartup.user_id == user.id,
                SavedStartup.startup_id == startup.id,
            )
        )
        existing = result.first()

        if existing:
            await self.db.delete(existing)
            return {"saved": False, "startup_id": startup.id}
        else:
            save = SavedStartup(
                id=str(uuid.uuid4()),
                user_id=user.id,
                startup_id=startup.id,
            )
            self.db.add(save)
            return {"saved": True, "startup_id": startup.id}

    async def get_saved(self, user: User) -> list[dict]:
        result = await self.db.exec(
            select(Startup)
            .join(SavedStartup, SavedStartup.startup_id == Startup.id)
            .where(SavedStartup.user_id == user.id, Startup.is_active == True)
            .order_by(SavedStartup.created_at.desc())
        )
        startups = result.all()
        return [
            {
                "id": s.id,
                "slug": s.slug,
                "name": s.name,
                "tagline": s.tagline,
                "logo_emoji": s.logo_emoji,
                "logo_color": s.logo_color,
                "category": s.category.value,
                "mrr_usd": s.mrr_usd,
                "is_verified": s.is_verified,
            }
            for s in startups
        ]
