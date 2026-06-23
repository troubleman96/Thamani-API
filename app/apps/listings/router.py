from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import ok, fail, ApiResponse
from app.core.pagination import PaginationParams
from app.apps.listings.schemas import ListingCreateIn, ListingUpdateIn, ListingOut
from app.apps.listings.service import ListingService
from app.apps.users.models import User

router = APIRouter(prefix="/listings", tags=["Listings / Marketplace"])


@router.get("", response_model=ApiResponse[list[ListingOut]])
async def list_active_listings(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    country: Optional[str] = None,
    min_mrr: Optional[float] = None,
    max_mrr: Optional[float] = None,
    min_multiple: Optional[float] = None,
    max_multiple: Optional[float] = None,
    sort_by: str = Query(
        "buyer_views",
        pattern="^(buyer_views|created_at|asking_price_usd|revenue_multiple)$",
    ),
    db: AsyncSession = Depends(get_db),
):
    service = ListingService(db)
    params = PaginationParams(page=page, per_page=per_page)
    items, meta = await service.list_active(
        params=params,
        category=category,
        country=country,
        min_mrr=min_mrr,
        max_mrr=max_mrr,
        min_multiple=min_multiple,
        max_multiple=max_multiple,
        sort_by=sort_by,
    )
    return ok(data=items, message="Listings retrieved successfully", meta=meta.model_dump())


@router.post("/{startup_slug}", response_model=ApiResponse[ListingOut])
async def create_listing(
    startup_slug: str,
    body: ListingCreateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ListingService(db)
    listing = await service.create(startup_slug=startup_slug, founder=current_user, data=body)
    if not listing:
        return fail("Startup not found, not yours, or not verified yet")
    return ok(data=listing, message="Startup listed for sale successfully")


@router.patch("/{startup_slug}", response_model=ApiResponse[ListingOut])
async def update_listing(
    startup_slug: str,
    body: ListingUpdateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ListingService(db)
    listing = await service.update(startup_slug=startup_slug, founder=current_user, data=body)
    if not listing:
        return fail("Listing not found or not yours")
    return ok(data=listing, message="Listing updated successfully")


@router.delete("/{startup_slug}", response_model=ApiResponse[None])
async def remove_listing(
    startup_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ListingService(db)
    removed = await service.delist(startup_slug=startup_slug, founder=current_user)
    if not removed:
        return fail("Listing not found or not yours")
    return ok(message="Startup delisted from marketplace")
