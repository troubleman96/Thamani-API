from datetime import date, timedelta
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.apps.revenue.models import RevenueSnapshot
from app.apps.revenue.schemas import RevenueHistoryOut, RevenueSnapshotOut
from app.apps.startups.models import Startup


class RevenueService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_history(
        self, startup_slug: str, days: int
    ) -> RevenueHistoryOut | None:
        result = await self.db.exec(
            select(Startup).where(Startup.slug == startup_slug, Startup.is_active == True)
        )
        startup = result.first()
        if not startup:
            return None

        since = date.today() - timedelta(days=days)
        result = await self.db.exec(
            select(RevenueSnapshot)
            .where(
                RevenueSnapshot.startup_id == startup.id,
                RevenueSnapshot.snapshot_date >= since,
            )
            .order_by(RevenueSnapshot.snapshot_date)
        )
        snapshots = result.all()

        return RevenueHistoryOut(
            startup_id=startup.id,
            startup_name=startup.name,
            verification_source=startup.verification_source or "unverified",
            tracked_since=startup.tracked_since.date() if startup.tracked_since else None,
            snapshots=[
                RevenueSnapshotOut(
                    snapshot_date=s.snapshot_date,
                    revenue_usd=s.revenue_usd,
                    charges_count=s.charges_count,
                    currency_local=s.currency_local,
                    revenue_local=s.revenue_local,
                    source=s.source,
                )
                for s in snapshots
            ],
            mrr_usd=startup.mrr_usd,
            arr_usd=startup.arr_usd,
            mom_growth_pct=startup.mom_growth_pct,
        )
