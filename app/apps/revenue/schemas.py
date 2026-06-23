from pydantic import BaseModel
from datetime import date
from typing import Optional


class RevenueSnapshotOut(BaseModel):
    snapshot_date: date
    revenue_usd: float
    charges_count: int
    currency_local: str
    revenue_local: float
    source: str


class RevenueHistoryOut(BaseModel):
    startup_id: str
    startup_name: str
    verification_source: str
    tracked_since: Optional[date]
    snapshots: list[RevenueSnapshotOut]
    mrr_usd: float
    arr_usd: float
    mom_growth_pct: Optional[float]
