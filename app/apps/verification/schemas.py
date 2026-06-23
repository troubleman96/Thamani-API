from pydantic import BaseModel
from typing import Literal, Optional


class ConnectProviderIn(BaseModel):
    provider: Literal["M-Pesa", "Selcom", "AzamPay", "Stripe"]
    account_identifier: str
    secret_key: str


class VerificationStatusOut(BaseModel):
    startup_id: str
    provider: str
    account_identifier: str
    is_active: bool
    last_verified_at: Optional[str]
    last_sync_status: str
