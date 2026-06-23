from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_db
from app.core.response import ok, ApiResponse
from app.apps.stats.schemas import PlatformStatsOut
from app.apps.stats.service import StatsService

router = APIRouter(prefix="/stats", tags=["Platform Stats"])


@router.get("", response_model=ApiResponse[PlatformStatsOut])
async def get_platform_stats(db: AsyncSession = Depends(get_db)):
    """Platform-wide aggregate stats, Redis-cached for 10 minutes."""
    service = StatsService(db)
    data = await service.get_platform_stats()
    return ok(data=data, message="Platform stats retrieved successfully")
