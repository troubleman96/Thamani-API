from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid
from enum import Enum


class OfferStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Offer(SQLModel, table=True):
    __tablename__ = "offers"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    listing_id: str = Field(foreign_key="listings.id", index=True)
    buyer_id: str = Field(foreign_key="users.id", index=True)
    offer_price_usd: float
    message: Optional[str] = None
    status: OfferStatus = Field(default=OfferStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
