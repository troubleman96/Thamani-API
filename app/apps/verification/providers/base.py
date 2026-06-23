from abc import ABC, abstractmethod
from datetime import date


class RevenueRecord:
    def __init__(
        self,
        snapshot_date: date,
        revenue_local: float,
        revenue_usd: float,
        charges_count: int,
        currency_local: str,
        exchange_rate: float,
    ):
        self.snapshot_date = snapshot_date
        self.revenue_local = revenue_local
        self.revenue_usd = revenue_usd
        self.charges_count = charges_count
        self.currency_local = currency_local
        self.exchange_rate = exchange_rate


class BaseRevenueProvider(ABC):
    """All payment provider adapters implement this interface."""

    provider_name: str

    def __init__(self, account_identifier: str, secret_key: str):
        self.account_identifier = account_identifier
        self.secret_key = secret_key

    @abstractmethod
    async def fetch_revenue(self, since: date, until: date) -> list[RevenueRecord]:
        """Fetch daily revenue records for the given date range."""
        ...

    @abstractmethod
    async def verify_credentials(self) -> bool:
        """Test that credentials are valid and the account is reachable."""
        ...
