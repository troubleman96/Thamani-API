from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class ListingCreateIn(BaseModel):
    asking_price_usd: float
    founder_message: str
    ttm_profit_usd: Optional[float] = None

    @field_validator("asking_price_usd")
    @classmethod
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError("Asking price must be positive")
        return v


class ListingUpdateIn(BaseModel):
    asking_price_usd: Optional[float] = None
    founder_message: Optional[str] = None
    ttm_profit_usd: Optional[float] = None


class ListingOut(BaseModel):
    id: str
    startup_id: str
    asking_price_usd: float
    revenue_multiple: float
    ttm_profit_usd: Optional[float]
    founder_message: str
    affiliate_earnings_usd: float
    offers_received: int
    buyer_views: int
    is_active: bool
    created_at: datetime
