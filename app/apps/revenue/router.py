from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_db
from app.core.response import ok, fail, ApiResponse
from app.apps.revenue.schemas import RevenueHistoryOut
from app.apps.revenue.service import RevenueService

router = APIRouter(prefix="/revenue", tags=["Revenue"])


@router.get("/{startup_slug}", response_model=ApiResponse[RevenueHistoryOut])
async def get_revenue_history(
    startup_slug: str,
    days: int = Query(30, ge=7, le=365, description="Number of days of history"),
    db: AsyncSession = Depends(get_db),
):
    service = RevenueService(db)
    data = await service.get_history(startup_slug=startup_slug, days=days)
    if not data:
        return fail("Startup not found or no revenue data yet")
    return ok(data=data, message="Revenue history retrieved successfully")
