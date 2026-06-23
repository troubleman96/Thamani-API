from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_optional_user
from app.core.response import ok, fail, ApiResponse
from app.core.pagination import PaginationParams
from app.apps.startups.schemas import (
    StartupCreateIn, StartupUpdateIn, StartupOut, StartupListOut,
)
from app.apps.startups.service import StartupService
from app.apps.startups.models import StartupCategory, StartupCountry
from app.apps.users.models import User

router = APIRouter(prefix="/startups", tags=["Startups"])


@router.get("", response_model=ApiResponse[list[StartupListOut]])
async def list_startups(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[StartupCategory] = None,
    country: Optional[StartupCountry] = None,
    is_for_sale: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    min_mrr: Optional[float] = None,
    max_mrr: Optional[float] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(mrr_usd|created_at|mom_growth_pct|last_30d_revenue_usd)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    service = StartupService(db)
    params = PaginationParams(page=page, per_page=per_page)
    items, meta = await service.list_startups(
        params=params,
        category=category,
        country=country,
        is_for_sale=is_for_sale,
        is_verified=is_verified,
        min_mrr=min_mrr,
        max_mrr=max_mrr,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return ok(data=items, message="Startups retrieved successfully", meta=meta.model_dump())


@router.post("", response_model=ApiResponse[StartupOut])
async def create_startup(
    body: StartupCreateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StartupService(db)
    startup = await service.create_startup(founder=current_user, data=body)
    return ok(data=startup, message="Startup created successfully")


@router.get("/mine", response_model=ApiResponse[list[StartupListOut]])
async def get_my_startups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StartupService(db)
    items = await service.get_by_founder(founder_id=current_user.id)
    return ok(data=items, message="Your startups retrieved successfully")


@router.get("/{slug}", response_model=ApiResponse[StartupOut])
async def get_startup(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    service = StartupService(db)
    startup = await service.get_by_slug(slug=slug)
    if not startup:
        return fail("Startup not found", errors=[f"No startup with slug '{slug}'"])
    return ok(data=startup, message="Startup retrieved successfully")


@router.patch("/{slug}", response_model=ApiResponse[StartupOut])
async def update_startup(
    slug: str,
    body: StartupUpdateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StartupService(db)
    startup = await service.update_startup(slug=slug, founder=current_user, data=body)
    if not startup:
        return fail("Startup not found or not yours")
    return ok(data=startup, message="Startup updated successfully")


@router.delete("/{slug}", response_model=ApiResponse[None])
async def delete_startup(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StartupService(db)
    deleted = await service.delete_startup(slug=slug, founder=current_user)
    if not deleted:
        return fail("Startup not found or not yours")
    return ok(message="Startup deleted successfully")
