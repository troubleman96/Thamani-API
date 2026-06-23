from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from app.apps.startups.models import Startup


class Listing(SQLModel, table=True):
    __tablename__ = "listings"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    startup_id: str = Field(foreign_key="startups.id", unique=True, index=True)
    asking_price_usd: float
    revenue_multiple: float
    ttm_profit_usd: Optional[float] = None
    founder_message: str
    affiliate_earnings_usd: float = Field(default=0.0)
    offers_received: int = Field(default=0)
    buyer_views: int = Field(default=0)
    is_active: bool = Field(default=True)
    sold_at: Optional[datetime] = None
    sold_price_usd: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    startup: Optional["Startup"] = Relationship(back_populates="listing")
