import httpx
from datetime import date
from app.apps.verification.providers.base import BaseRevenueProvider, RevenueRecord
from app.core.config import settings

MPESA_SANDBOX_URL = "https://sandbox.safaricom.co.ke"
MPESA_PROD_URL = "https://api.safaricom.co.ke"

TZS_TO_USD = 0.00038


class MpesaProvider(BaseRevenueProvider):
    provider_name = "M-Pesa"

    def __init__(self, account_identifier: str, secret_key: str):
        super().__init__(account_identifier, secret_key)
        self.base_url = (
            MPESA_PROD_URL if settings.MPESA_ENV == "production" else MPESA_SANDBOX_URL
        )

    async def _get_access_token(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials",
                auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
            )
            resp.raise_for_status()
            return resp.json()["access_token"]

    async def verify_credentials(self) -> bool:
        try:
            await self._get_access_token()
            return True
        except Exception:
            return False

    async def fetch_revenue(self, since: date, until: date) -> list[RevenueRecord]:
        # Daraja Transaction Status / Account Balance queries are used in production.
        # This stub returns an empty list — implement with Daraja B2C/STK query APIs.
        return []
