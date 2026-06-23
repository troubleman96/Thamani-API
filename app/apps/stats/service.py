import json
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from app.apps.stats.schemas import PlatformStatsOut
from app.apps.startups.models import Startup
from app.apps.listings.models import Listing
from app.core.redis import get_redis

STATS_TTL = 600  # 10 minutes
CACHE_KEY = "platform:stats"


class StatsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_platform_stats(self) -> PlatformStatsOut:
        redis = await get_redis()
        cached = await redis.get(CACHE_KEY)
        if cached:
            return PlatformStatsOut(**json.loads(cached))

        result = await self.db.exec(
            select(
                func.count(Startup.id),
                func.sum(Startup.is_verified.cast(int) if hasattr(Startup.is_verified, 'cast') else Startup.is_verified),
                func.coalesce(func.sum(Startup.mrr_usd), 0.0),
                func.coalesce(func.sum(Startup.arr_usd), 0.0),
            ).where(Startup.is_active == True)
        )
        row = result.one()
        total_startups = row[0] or 0
        verified_startups = row[1] or 0
        total_mrr = float(row[2] or 0)
        total_arr = float(row[3] or 0)

        listing_result = await self.db.exec(
            select(
                func.count(Listing.id),
                func.count(Listing.sold_at),
                func.coalesce(func.sum(Listing.sold_price_usd), 0.0),
            )
        )
        lrow = listing_result.one()
        for_sale_count = lrow[0] or 0
        deals_closed = lrow[1] or 0
        deal_value = float(lrow[2] or 0)

        by_country_result = await self.db.exec(
            select(Startup.country, func.count(Startup.id), func.coalesce(func.sum(Startup.mrr_usd), 0.0))
            .where(Startup.is_active == True)
            .group_by(Startup.country)
        )
        by_country = {}
        for row in by_country_result.all():
            by_country[row[0].value if hasattr(row[0], 'value') else row[0]] = {
                "count": row[1],
                "mrr_usd": float(row[2]),
            }

        by_category_result = await self.db.exec(
            select(Startup.category, func.count(Startup.id), func.coalesce(func.sum(Startup.mrr_usd), 0.0))
            .where(Startup.is_active == True)
            .group_by(Startup.category)
        )
        by_category = {}
        for row in by_category_result.all():
            by_category[row[0].value if hasattr(row[0], 'value') else row[0]] = {
                "count": row[1],
                "mrr_usd": float(row[2]),
            }

        top_growth_result = await self.db.exec(
            select(Startup)
            .where(Startup.is_active == True, Startup.mom_growth_pct != None)
            .order_by(Startup.mom_growth_pct.desc())
            .limit(5)
        )
        top_growth = [
            {
                "id": s.id,
                "slug": s.slug,
                "name": s.name,
                "mom_growth_pct": s.mom_growth_pct,
                "mrr_usd": s.mrr_usd,
            }
            for s in top_growth_result.all()
        ]

        stats = PlatformStatsOut(
            total_startups=total_startups,
            verified_startups=verified_startups,
            total_mrr_usd=total_mrr,
            total_arr_usd=total_arr,
            for_sale_count=for_sale_count,
            total_deals_closed=deals_closed,
            total_deal_value_usd=deal_value,
            by_country=by_country,
            by_category=by_category,
            top_growth_startups=top_growth,
        )

        await redis.setex(CACHE_KEY, STATS_TTL, json.dumps(stats.model_dump()))
        return stats
