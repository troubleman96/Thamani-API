import uuid
from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.apps.offers.models import Offer, OfferStatus
from app.apps.offers.schemas import OfferCreateIn, OfferOut
from app.apps.listings.models import Listing
from app.apps.startups.models import Startup
from app.apps.users.models import User


def _to_out(offer: Offer) -> OfferOut:
    return OfferOut(
        id=offer.id,
        listing_id=offer.listing_id,
        buyer_id=offer.buyer_id,
        offer_price_usd=offer.offer_price_usd,
        message=offer.message,
        status=offer.status.value,
    )


class OfferService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_offer(self, buyer: User, data: OfferCreateIn) -> OfferOut | None:
        result = await self.db.exec(
            select(Listing).where(
                Listing.id == data.listing_id,
                Listing.is_active == True,
            )
        )
        listing = result.first()
        if not listing:
            return None

        offer = Offer(
            id=str(uuid.uuid4()),
            listing_id=data.listing_id,
            buyer_id=buyer.id,
            offer_price_usd=data.offer_price_usd,
            message=data.message,
        )
        self.db.add(offer)

        listing.offers_received += 1
        self.db.add(listing)

        return _to_out(offer)

    async def get_received(self, founder: User) -> list[OfferOut]:
        result = await self.db.exec(
            select(Offer)
            .join(Listing, Listing.id == Offer.listing_id)
            .join(Startup, Startup.id == Listing.startup_id)
            .where(Startup.founder_id == founder.id)
            .order_by(Offer.created_at.desc())
        )
        return [_to_out(o) for o in result.all()]

    async def _change_status(
        self, offer_id: str, founder: User, new_status: OfferStatus
    ) -> OfferOut | None:
        result = await self.db.exec(
            select(Offer)
            .join(Listing, Listing.id == Offer.listing_id)
            .join(Startup, Startup.id == Listing.startup_id)
            .where(Offer.id == offer_id, Startup.founder_id == founder.id)
        )
        offer = result.first()
        if not offer:
            return None
        offer.status = new_status
        offer.updated_at = datetime.utcnow()
        self.db.add(offer)

        if new_status == OfferStatus.ACCEPTED:
            result2 = await self.db.exec(
                select(Listing).where(Listing.id == offer.listing_id)
            )
            listing = result2.first()
            if listing:
                listing.sold_at = datetime.utcnow()
                listing.sold_price_usd = offer.offer_price_usd
                listing.is_active = False
                self.db.add(listing)

        return _to_out(offer)

    async def accept(self, offer_id: str, founder: User) -> OfferOut | None:
        return await self._change_status(offer_id, founder, OfferStatus.ACCEPTED)

    async def reject(self, offer_id: str, founder: User) -> OfferOut | None:
        return await self._change_status(offer_id, founder, OfferStatus.REJECTED)
