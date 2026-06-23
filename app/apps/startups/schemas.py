from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from app.apps.startups.models import StartupCategory, StartupCountry


class StartupCreateIn(BaseModel):
    name: str
    tagline: str
    description: str
    category: StartupCategory
    country: StartupCountry = StartupCountry.TANZANIA
    founded_date: str
    logo_emoji: Optional[str] = None
    logo_color: str = "#6366F1"
    website_url: Optional[str] = None
    tech_stack_frontend: list[str] = []
    tech_stack_backend: list[str] = []
    marketing_channels: list[str] = []
    market_segments: list[str] = []

    @field_validator("name")
    @classmethod
    def name_min_length(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Startup name must be at least 2 characters")
        return v.strip()


class StartupUpdateIn(BaseModel):
    tagline: Optional[str] = None
    description: Optional[str] = None
    category: Optional[StartupCategory] = None
    logo_emoji: Optional[str] = None
    logo_color: Optional[str] = None
    website_url: Optional[str] = None
    tech_stack_frontend: Optional[list[str]] = None
    tech_stack_backend: Optional[list[str]] = None
    marketing_channels: Optional[list[str]] = None
    market_segments: Optional[list[str]] = None


class FounderOut(BaseModel):
    id: str
    full_name: str
    avatar_url: Optional[str]
    country: str


class ListingBriefOut(BaseModel):
    asking_price_usd: float
    revenue_multiple: float
    offers_received: int
    buyer_views: int


class StartupOut(BaseModel):
    id: str
    slug: str
    name: str
    tagline: str
    description: str
    logo_emoji: Optional[str]
    logo_color: str
    logo_url: Optional[str]
    category: str
    country: str
    founded_date: str
    founder: Optional[FounderOut]
    mrr_usd: float
    arr_usd: float
    last_30d_revenue_usd: float
    active_subscriptions: int
    mom_growth_pct: Optional[float]
    is_verified: bool
    verification_source: Optional[str]
    verified_at: Optional[datetime]
    tracked_since: Optional[datetime]
    last_synced_at: Optional[datetime]
    tech_stack_frontend: list[str]
    tech_stack_backend: list[str]
    marketing_channels: list[str]
    market_segments: list[str]
    is_for_sale: bool
    listing: Optional[ListingBriefOut]
    created_at: datetime


class StartupListOut(BaseModel):
    id: str
    slug: str
    name: str
    tagline: str
    logo_emoji: Optional[str]
    logo_color: str
    category: str
    country: str
    mrr_usd: float
    mom_growth_pct: Optional[float]
    is_verified: bool
    verification_source: Optional[str]
    is_for_sale: bool
    listing: Optional[ListingBriefOut]
