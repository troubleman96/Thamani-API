from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, date
import uuid

if TYPE_CHECKING:
    from app.apps.startups.models import Startup


class RevenueSnapshot(SQLModel, table=True):
    """One row per day per startup. Append-only — never update existing rows."""
    __tablename__ = "revenue_snapshots"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    startup_id: str = Field(foreign_key="startups.id", index=True)
    snapshot_date: date = Field(index=True)
    revenue_usd: float
    charges_count: int
    currency_local: str
    revenue_local: float
    exchange_rate: float
    source: str
    raw_payload: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    startup: Optional["Startup"] = Relationship(back_populates="revenue_snapshots")
