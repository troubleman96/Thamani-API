import hmac
import hashlib
import base64
from datetime import date, datetime
import httpx
from app.apps.verification.providers.base import BaseRevenueProvider, RevenueRecord

SELCOM_BASE_URL = "https://apigw.selcom.net"

TZS_TO_USD = 0.00038


class SelcomProvider(BaseRevenueProvider):
    provider_name = "Selcom"

    def _auth_headers(self, timestamp: str) -> dict:
        signed = hmac.new(
            self.secret_key.encode(),
            timestamp.encode(),
            hashlib.sha256,
        ).digest()
        signature = base64.b64encode(signed).decode()
        return {
            "Authorization": f"SELCOM {self.account_identifier}:{signature}",
            "Digest-Method": "HS256",
            "Timestamp": timestamp,
            "Content-Type": "application/json",
        }

    async def verify_credentials(self) -> bool:
        try:
            ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{SELCOM_BASE_URL}/v1/checkout/list-orders",
                    headers=self._auth_headers(ts),
                    timeout=10,
                )
                return resp.status_code in (200, 201)
        except Exception:
            return False

    async def fetch_revenue(self, since: date, until: date) -> list[RevenueRecord]:
        # Implement with Selcom order-list API filtered by date range
        return []
