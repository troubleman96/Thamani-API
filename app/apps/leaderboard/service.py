import json
from datetime import date, timedelta
from sqlmodel import select
from sqlalchemy import desc
from sqlmodel.ext.asyncio.session import AsyncSession
from app.apps.leaderboard.schemas import LeaderboardEntryOut
from app.apps.startups.models import Startup
from app.apps.listings.models import Listing
from app.apps.users.models import User
from app.core.redis import get_redis

LEADERBOARD_TTL = 300  # 5 minutes


class LeaderboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _cache_key(self, metric: str, period: str, country: str | None, category: str | None, limit: int) -> str:
        return f"leaderboard:{metric}:{period}:{country or 'all'}:{category or 'all'}:{limit}"

    async def get_leaderboard(
        self,
        metric: str,
        period: str,
        country: str | None,
        category: str | None,
        limit: int,
    ) -> list[LeaderboardEntryOut]:
        redis = await get_redis()
        cache_key = self._cache_key(metric, period, country, category, limit)

        cached = await redis.get(cache_key)
        if cached:
            raw = json.loads(cached)
            return [LeaderboardEntryOut(**item) for item in raw]

        query = (
            select(Startup)
            .join(User, User.id == Startup.founder_id)
            .where(Startup.is_active == True, Startup.is_public == True)
        )

        if period == "last_30d":
            cutoff = date.today() - timedelta(days=30)
            query = query.where(Startup.tracked_since >= cutoff)
        elif period == "last_90d":
            cutoff = date.today() - timedelta(days=90)
            query = query.where(Startup.tracked_since >= cutoff)

        if country:
            query = query.where(Startup.country == country)
        if category:
            query = query.where(Startup.category == category)

        sort_col = getattr(Startup, metric, Startup.mrr_usd)
        query = query.order_by(desc(sort_col)).limit(limit)

        result = await self.db.exec(query)
        startups = result.all()

        active_listing_ids = set()
        if startups:
            listing_result = await self.db.exec(
                select(Listing.startup_id).where(
                    Listing.startup_id.in_([s.id for s in startups]),
                    Listing.is_active == True,
                )
            )
            active_listing_ids = set(listing_result.all())

        entries = []
        for rank, startup in enumerate(startups, start=1):
            founder = startup.founder
            entries.append(
                LeaderboardEntryOut(
                    rank=rank,
                    startup_id=startup.id,
                    slug=startup.slug,
                    name=startup.name,
                    tagline=startup.tagline,
                    logo_emoji=startup.logo_emoji,
                    logo_color=startup.logo_color,
                    category=startup.category.value,
                    country=startup.country.value,
                    founder_name=founder.full_name if founder else "",
                    founder_avatar=founder.avatar_url if founder else None,
                    mrr_usd=startup.mrr_usd,
                    arr_usd=startup.arr_usd,
                    last_30d_revenue_usd=startup.last_30d_revenue_usd,
                    mom_growth_pct=startup.mom_growth_pct,
                    active_subscriptions=startup.active_subscriptions,
                    verification_source=startup.verification_source,
                    is_verified=startup.is_verified,
                    is_for_sale=startup.id in active_listing_ids,
                )
            )

        await redis.setex(cache_key, LEADERBOARD_TTL, json.dumps([e.model_dump() for e in entries]))
        return entries
