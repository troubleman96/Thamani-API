import re
import uuid
from datetime import datetime
from sqlmodel import select, or_
from sqlalchemy import asc, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from app.apps.startups.models import Startup, StartupCategory, StartupCountry
from app.apps.startups.schemas import (
    StartupCreateIn, StartupUpdateIn, StartupOut, StartupListOut,
    FounderOut, ListingBriefOut,
)
from app.apps.users.models import User
from app.core.pagination import PaginationParams, paginate, PaginationMeta


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


class StartupService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _build_out(self, startup: Startup) -> StartupOut:
        founder_out = None
        if startup.founder:
            founder_out = FounderOut(
                id=startup.founder.id,
                full_name=startup.founder.full_name,
                avatar_url=startup.founder.avatar_url,
                country=startup.founder.country,
            )

        listing_out = None
        is_for_sale = False
        if startup.listing and startup.listing.is_active:
            is_for_sale = True
            listing_out = ListingBriefOut(
                asking_price_usd=startup.listing.asking_price_usd,
                revenue_multiple=startup.listing.revenue_multiple,
                offers_received=startup.listing.offers_received,
                buyer_views=startup.listing.buyer_views,
            )

        return StartupOut(
            id=startup.id,
            slug=startup.slug,
            name=startup.name,
            tagline=startup.tagline,
            description=startup.description,
            logo_emoji=startup.logo_emoji,
            logo_color=startup.logo_color,
            logo_url=startup.logo_url,
            category=startup.category.value,
            country=startup.country.value,
            founded_date=startup.founded_date,
            founder=founder_out,
            mrr_usd=startup.mrr_usd,
            arr_usd=startup.arr_usd,
            last_30d_revenue_usd=startup.last_30d_revenue_usd,
            active_subscriptions=startup.active_subscriptions,
            mom_growth_pct=startup.mom_growth_pct,
            is_verified=startup.is_verified,
            verification_source=startup.verification_source,
            verified_at=startup.verified_at,
            tracked_since=startup.tracked_since,
            last_synced_at=startup.last_synced_at,
            tech_stack_frontend=startup.tech_stack_frontend or [],
            tech_stack_backend=startup.tech_stack_backend or [],
            marketing_channels=startup.marketing_channels or [],
            market_segments=startup.market_segments or [],
            is_for_sale=is_for_sale,
            listing=listing_out,
            created_at=startup.created_at,
        )

    def _build_list_out(self, startup: Startup) -> StartupListOut:
        listing_out = None
        is_for_sale = False
        if startup.listing and startup.listing.is_active:
            is_for_sale = True
            listing_out = ListingBriefOut(
                asking_price_usd=startup.listing.asking_price_usd,
                revenue_multiple=startup.listing.revenue_multiple,
                offers_received=startup.listing.offers_received,
                buyer_views=startup.listing.buyer_views,
            )
        return StartupListOut(
            id=startup.id,
            slug=startup.slug,
            name=startup.name,
            tagline=startup.tagline,
            logo_emoji=startup.logo_emoji,
            logo_color=startup.logo_color,
            category=startup.category.value,
            country=startup.country.value,
            mrr_usd=startup.mrr_usd,
            mom_growth_pct=startup.mom_growth_pct,
            is_verified=startup.is_verified,
            verification_source=startup.verification_source,
            is_for_sale=is_for_sale,
            listing=listing_out,
        )

    async def _unique_slug(self, base: str) -> str:
        slug = base
        result = await self.db.exec(select(Startup).where(Startup.slug == slug))
        if not result.first():
            return slug
        slug = f"{base}-{str(uuid.uuid4())[:8]}"
        return slug

    async def create_startup(self, founder: User, data: StartupCreateIn) -> StartupOut:
        base_slug = _slugify(data.name)
        slug = await self._unique_slug(base_slug)

        startup = Startup(
            id=str(uuid.uuid4()),
            slug=slug,
            name=data.name,
            tagline=data.tagline,
            description=data.description,
            category=data.category,
            country=data.country,
            founded_date=data.founded_date,
            founder_id=founder.id,
            logo_emoji=data.logo_emoji,
            logo_color=data.logo_color,
            website_url=data.website_url,
            tech_stack_frontend=data.tech_stack_frontend,
            tech_stack_backend=data.tech_stack_backend,
            marketing_channels=data.marketing_channels,
            market_segments=data.market_segments,
        )
        startup.founder = founder
        self.db.add(startup)
        await self.db.flush()
        return await self._build_out(startup)

    async def get_by_slug(self, slug: str) -> StartupOut | None:
        from sqlmodel import select
        result = await self.db.exec(
            select(Startup).where(Startup.slug == slug, Startup.is_active == True)
        )
        startup = result.first()
        if not startup:
            return None
        return await self._build_out(startup)

    async def get_by_founder(self, founder_id: str) -> list[StartupListOut]:
        result = await self.db.exec(
            select(Startup).where(
                Startup.founder_id == founder_id,
                Startup.is_active == True,
            )
        )
        return [self._build_list_out(s) for s in result.all()]

    async def list_startups(
        self,
        params: PaginationParams,
        category: StartupCategory | None,
        country: StartupCountry | None,
        is_for_sale: bool | None,
        is_verified: bool | None,
        min_mrr: float | None,
        max_mrr: float | None,
        search: str | None,
        sort_by: str,
        sort_dir: str,
    ) -> tuple[list[StartupListOut], PaginationMeta]:
        query = select(Startup).where(Startup.is_active == True, Startup.is_public == True)

        if category:
            query = query.where(Startup.category == category)
        if country:
            query = query.where(Startup.country == country)
        if is_verified is not None:
            query = query.where(Startup.is_verified == is_verified)
        if min_mrr is not None:
            query = query.where(Startup.mrr_usd >= min_mrr)
        if max_mrr is not None:
            query = query.where(Startup.mrr_usd <= max_mrr)
        if search:
            term = f"%{search}%"
            query = query.where(
                or_(Startup.name.ilike(term), Startup.tagline.ilike(term))
            )

        sort_col = getattr(Startup, sort_by)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))

        if is_for_sale is not None:
            from app.apps.listings.models import Listing
            if is_for_sale:
                query = query.join(Listing, Listing.startup_id == Startup.id).where(
                    Listing.is_active == True
                )
            else:
                from sqlalchemy import not_, exists
                sub = select(Listing.startup_id).where(Listing.is_active == True)
                query = query.where(not_(Startup.id.in_(sub)))

        items, meta = await paginate(self.db, query, params)
        return [self._build_list_out(s) for s in items], meta

    async def update_startup(
        self, slug: str, founder: User, data: StartupUpdateIn
    ) -> StartupOut | None:
        result = await self.db.exec(
            select(Startup).where(
                Startup.slug == slug,
                Startup.founder_id == founder.id,
                Startup.is_active == True,
            )
        )
        startup = result.first()
        if not startup:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(startup, field, value)
        startup.updated_at = datetime.utcnow()
        self.db.add(startup)
        return await self._build_out(startup)

    async def delete_startup(self, slug: str, founder: User) -> bool:
        result = await self.db.exec(
            select(Startup).where(
                Startup.slug == slug,
                Startup.founder_id == founder.id,
                Startup.is_active == True,
            )
        )
        startup = result.first()
        if not startup:
            return False
        startup.is_active = False
        startup.updated_at = datetime.utcnow()
        self.db.add(startup)
        return True
