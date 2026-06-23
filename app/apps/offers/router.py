from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import ok, fail, ApiResponse
from app.apps.offers.schemas import OfferCreateIn, OfferOut
from app.apps.offers.service import OfferService
from app.apps.users.models import User

router = APIRouter(prefix="/offers", tags=["Offers"])


@router.post("", response_model=ApiResponse[OfferOut])
async def make_offer(
    body: OfferCreateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OfferService(db)
    offer = await service.create_offer(buyer=current_user, data=body)
    if not offer:
        return fail("Listing not found or not active")
    return ok(data=offer, message="Offer submitted successfully")


@router.get("/received", response_model=ApiResponse[list[OfferOut]])
async def get_received_offers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OfferService(db)
    offers = await service.get_received(founder=current_user)
    return ok(data=offers, message="Received offers retrieved successfully")


@router.patch("/{offer_id}/accept", response_model=ApiResponse[OfferOut])
async def accept_offer(
    offer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OfferService(db)
    offer = await service.accept(offer_id=offer_id, founder=current_user)
    if not offer:
        return fail("Offer not found or not yours to accept")
    return ok(data=offer, message="Offer accepted")


@router.patch("/{offer_id}/reject", response_model=ApiResponse[OfferOut])
async def reject_offer(
    offer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OfferService(db)
    offer = await service.reject(offer_id=offer_id, founder=current_user)
    if not offer:
        return fail("Offer not found or not yours")
    return ok(data=offer, message="Offer rejected")
