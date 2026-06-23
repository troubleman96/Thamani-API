from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from typing import Optional, TYPE_CHECKING
from datetime import datetime
import uuid
from enum import Enum

if TYPE_CHECKING:
    from app.apps.users.models import User
    from app.apps.revenue.models import RevenueSnapshot
    from app.apps.listings.models import Listing


class StartupCategory(str, Enum):
    SAAS = "SaaS"
    AGRITECH = "AgriTech"
    FINTECH = "FinTech"
    HEALTHTECH = "HealthTech"
    EDUTECH = "EduTech"
    LOGISTICS = "Logistics"
    ECOMMERCE = "E-Commerce"
    REAL_ESTATE = "Real Estate"
    MOBILE_APPS = "Mobile Apps"
    AI_ML = "AI / ML"
    ENTERTAINMENT = "Entertainment"
    DEVELOPER_TOOLS = "Developer Tools"


class StartupCountry(str, Enum):
    TANZANIA = "Tanzania"
    KENYA = "Kenya"
    UGANDA = "Uganda"
    RWANDA = "Rwanda"
    ETHIOPIA = "Ethiopia"


class Startup(SQLModel, table=True):
    __tablename__ = "startups"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str = Field(index=True)
    tagline: str
    description: str
    logo_emoji: Optional[str] = None
    logo_color: str = Field(default="#6366F1")
    logo_url: Optional[str] = None
    category: StartupCategory
    country: StartupCountry = Field(default=StartupCountry.TANZANIA)
    founded_date: str
    founder_id: str = Field(foreign_key="users.id", index=True)
    website_url: Optional[str] = None

    mrr_usd: float = Field(default=0.0)
    arr_usd: float = Field(default=0.0)
    last_30d_revenue_usd: float = Field(default=0.0)
    active_subscriptions: int = Field(default=0)
    mom_growth_pct: Optional[float] = None

    is_verified: bool = Field(default=False)
    verification_source: Optional[str] = None
    verified_at: Optional[datetime] = None
    tracked_since: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None

    tech_stack_frontend: list[str] = Field(default=[], sa_column=Column(JSON))
    tech_stack_backend: list[str] = Field(default=[], sa_column=Column(JSON))
    marketing_channels: list[str] = Field(default=[], sa_column=Column(JSON))
    market_segments: list[str] = Field(default=[], sa_column=Column(JSON))

    is_active: bool = Field(default=True)
    is_public: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    founder: Optional["User"] = Relationship(back_populates="startups")
    revenue_snapshots: list["RevenueSnapshot"] = Relationship(back_populates="startup")
    listing: Optional["Listing"] = Relationship(back_populates="startup")
