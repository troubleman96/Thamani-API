import httpx
from datetime import date, datetime, timezone
from app.apps.verification.providers.base import BaseRevenueProvider, RevenueRecord

STRIPE_BASE_URL = "https://api.stripe.com/v1"

USD_DIVISOR = 100  # Stripe amounts are in cents


class StripeProvider(BaseRevenueProvider):
    provider_name = "Stripe"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.secret_key}"}

    async def verify_credentials(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{STRIPE_BASE_URL}/balance",
                    headers=self._headers(),
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def fetch_revenue(self, since: date, until: date) -> list[RevenueRecord]:
        since_ts = int(datetime(since.year, since.month, since.day, tzinfo=timezone.utc).timestamp())
        until_ts = int(datetime(until.year, until.month, until.day, 23, 59, 59, tzinfo=timezone.utc).timestamp())

        charges: list[dict] = []
        params = {
            "created[gte]": since_ts,
            "created[lte]": until_ts,
            "limit": 100,
        }

        async with httpx.AsyncClient() as client:
            while True:
                resp = await client.get(
                    f"{STRIPE_BASE_URL}/charges",
                    headers=self._headers(),
                    params=params,
                )
                resp.raise_for_status()
                body = resp.json()
                charges.extend(body["data"])
                if not body["has_more"]:
                    break
                params["starting_after"] = charges[-1]["id"]

        by_day: dict[date, tuple[float, int]] = {}
        for charge in charges:
            if charge.get("paid") and not charge.get("refunded"):
                d = datetime.fromtimestamp(charge["created"], tz=timezone.utc).date()
                usd = charge["amount"] / USD_DIVISOR
                prev_usd, prev_count = by_day.get(d, (0.0, 0))
                by_day[d] = (prev_usd + usd, prev_count + 1)

        return [
            RevenueRecord(
                snapshot_date=d,
                revenue_local=usd,
                revenue_usd=usd,
                charges_count=count,
                currency_local="USD",
                exchange_rate=1.0,
            )
            for d, (usd, count) in sorted(by_day.items())
        ]
