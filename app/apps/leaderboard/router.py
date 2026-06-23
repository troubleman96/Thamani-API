from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.core.response import ok, ApiResponse
from app.apps.leaderboard.schemas import LeaderboardEntryOut
from app.apps.leaderboard.service import LeaderboardService

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get("", response_model=ApiResponse[list[LeaderboardEntryOut]])
async def get_leaderboard(
    metric: str = Query("mrr_usd", pattern="^(mrr_usd|arr_usd|last_30d_revenue_usd)$"),
    period: str = Query("all_time", pattern="^(all_time|last_90d|last_30d)$"),
    country: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(50, ge=5, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Ranked startup leaderboard, Redis-cached for 5 minutes."""
    service = LeaderboardService(db)
    entries = await service.get_leaderboard(
        metric=metric,
        period=period,
        country=country,
        category=category,
        limit=limit,
    )
    return ok(
        data=entries,
        message="Leaderboard retrieved successfully",
        meta={"metric": metric, "period": period, "total": len(entries)},
    )
