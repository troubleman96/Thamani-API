from pydantic import BaseModel
from typing import Any


class PlatformStatsOut(BaseModel):
    total_startups: int
    verified_startups: int
    total_mrr_usd: float
    total_arr_usd: float
    for_sale_count: int
    total_deals_closed: int
    total_deal_value_usd: float
    by_country: dict[str, Any]
    by_category: dict[str, Any]
    top_growth_startups: list[dict]
