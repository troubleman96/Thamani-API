from pydantic import BaseModel
from typing import Optional


class LeaderboardEntryOut(BaseModel):
    rank: int
    startup_id: str
    slug: str
    name: str
    tagline: str
    logo_emoji: Optional[str]
    logo_color: str
    category: str
    country: str
    founder_name: str
    founder_avatar: Optional[str]
    mrr_usd: float
    arr_usd: float
    last_30d_revenue_usd: float
    mom_growth_pct: Optional[float]
    active_subscriptions: int
    verification_source: Optional[str]
    is_verified: bool
    is_for_sale: bool
