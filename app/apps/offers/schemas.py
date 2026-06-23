from pydantic import BaseModel, field_validator
from typing import Optional


class OfferCreateIn(BaseModel):
    listing_id: str
    offer_price_usd: float
    message: Optional[str] = None

    @field_validator("offer_price_usd")
    @classmethod
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError("Offer price must be positive")
        return v


class OfferOut(BaseModel):
    id: str
    listing_id: str
    buyer_id: str
    offer_price_usd: float
    message: Optional[str]
    status: str
