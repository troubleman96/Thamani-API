import uuid
from datetime import datetime
from sqlmodel import select
from sqlalchemy import asc, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from app.apps.listings.models import Listing
from app.apps.listings.schemas import ListingCreateIn, ListingUpdateIn, ListingOut
from app.apps.startups.models import Startup, StartupCategory, StartupCountry
from app.apps.users.models import User
from app.core.pagination import PaginationParams, paginate, PaginationMeta


def _to_out(listing: Listing) -> ListingOut:
    return ListingOut(
        id=listing.id,
        startup_id=listing.startup_id,
        asking_price_usd=listing.asking_price_usd,
        revenue_multiple=listing.revenue_multiple,
        ttm_profit_usd=listing.ttm_profit_usd,
        founder_message=listing.founder_message,
        affiliate_earnings_usd=listing.affiliate_earnings_usd,
        offers_received=listing.offers_received,
        buyer_views=listing.buyer_views,
        is_active=listing.is_active,
        created_at=listing.created_at,
    )


class ListingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, startup_slug: str, founder: User, data: ListingCreateIn
    ) -> ListingOut | None:
        result = await self.db.exec(
            select(Startup).where(
                Startup.slug == startup_slug,
                Startup.founder_id == founder.id,
                Startup.is_active == True,
                Startup.is_verified == True,
            )
        )
        startup = result.first()
        if not startup:
            return None

        multiple = (
            data.asking_price_usd / (startup.mrr_usd * 12)
            if startup.mrr_usd > 0
            else 0.0
        )

        result = await self.db.exec(
            select(Listing).where(Listing.startup_id == startup.id)
        )
        existing = result.first()
        if existing:
            existing.asking_price_usd = data.asking_price_usd
            existing.founder_message = data.founder_message
            existing.ttm_profit_usd = data.ttm_profit_usd
            existing.revenue_multiple = multiple
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
            self.db.add(existing)
            return _to_out(existing)

        listing = Listing(
            id=str(uuid.uuid4()),
            startup_id=startup.id,
            asking_price_usd=data.asking_price_usd,
            revenue_multiple=multiple,
            ttm_profit_usd=data.ttm_profit_usd,
            founder_message=data.founder_message,
        )
        self.db.add(listing)
        return _to_out(listing)

    async def list_active(
        self,
        params: PaginationParams,
        category: str | None,
        country: str | None,
        min_mrr: float | None,
        max_mrr: float | None,
        min_multiple: float | None,
        max_multiple: float | None,
        sort_by: str,
    ) -> tuple[list[ListingOut], PaginationMeta]:
        query = (
            select(Listing)
            .join(Startup, Startup.id == Listing.startup_id)
            .where(Listing.is_active == True, Startup.is_active == True)
        )

        if category:
            query = query.where(Startup.category == category)
        if country:
            query = query.where(Startup.country == country)
        if min_mrr is not None:
            query = query.where(Startup.mrr_usd >= min_mrr)
        if max_mrr is not None:
            query = query.where(Startup.mrr_usd <= max_mrr)
        if min_multiple is not None:
            query = query.where(Listing.revenue_multiple >= min_multiple)
        if max_multiple is not None:
            query = query.where(Listing.revenue_multiple <= max_multiple)

        sort_col = getattr(Listing, sort_by, Listing.buyer_views)
        query = query.order_by(desc(sort_col))

        items, meta = await paginate(self.db, query, params)
        return [_to_out(l) for l in items], meta

    async def update(
        self, startup_slug: str, founder: User, data: ListingUpdateIn
    ) -> ListingOut | None:
        result = await self.db.exec(
            select(Listing)
            .join(Startup, Startup.id == Listing.startup_id)
            .where(
                Startup.slug == startup_slug,
                Startup.founder_id == founder.id,
                Listing.is_active == True,
            )
        )
        listing = result.first()
        if not listing:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(listing, field, value)
        listing.updated_at = datetime.utcnow()
        self.db.add(listing)
        return _to_out(listing)

    async def delist(self, startup_slug: str, founder: User) -> bool:
        result = await self.db.exec(
            select(Listing)
            .join(Startup, Startup.id == Listing.startup_id)
            .where(
                Startup.slug == startup_slug,
                Startup.founder_id == founder.id,
                Listing.is_active == True,
            )
        )
        listing = result.first()
        if not listing:
            return False
        listing.is_active = False
        listing.updated_at = datetime.utcnow()
        self.db.add(listing)
        return True
