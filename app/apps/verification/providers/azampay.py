import httpx
from datetime import date
from app.apps.verification.providers.base import BaseRevenueProvider, RevenueRecord
from app.core.config import settings

AZAMPAY_SANDBOX_URL = "https://sandbox.azampay.co.tz"
AZAMPAY_PROD_URL = "https://api.azampay.co.tz"

TZS_TO_USD = 0.00038


class AzamPayProvider(BaseRevenueProvider):
    provider_name = "AzamPay"

    def __init__(self, account_identifier: str, secret_key: str):
        super().__init__(account_identifier, secret_key)
        self.base_url = (
            AZAMPAY_PROD_URL if settings.AZAMPAY_ENV == "production" else AZAMPAY_SANDBOX_URL
        )

    async def _get_token(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/AppRegistration/GenerateToken",
                json={
                    "appName": settings.AZAMPAY_APP_NAME,
                    "clientId": settings.AZAMPAY_CLIENT_ID,
                    "clientSecret": settings.AZAMPAY_CLIENT_SECRET,
                },
            )
            resp.raise_for_status()
            return resp.json()["data"]["accessToken"]

    async def verify_credentials(self) -> bool:
        try:
            await self._get_token()
            return True
        except Exception:
            return False

    async def fetch_revenue(self, since: date, until: date) -> list[RevenueRecord]:
        # Implement with AzamPay transaction history endpoint
        return []
