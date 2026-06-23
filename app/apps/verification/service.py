import base64
import uuid
from datetime import datetime, date, timedelta
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from cryptography.fernet import Fernet
from app.core.config import settings
from app.apps.verification.models import VerificationCredential
from app.apps.verification.schemas import ConnectProviderIn, VerificationStatusOut
from app.apps.startups.models import Startup
from app.apps.users.models import User
from app.apps.revenue.models import RevenueSnapshot


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32, b"0"))
    return Fernet(key)


def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_secret(cipher: str) -> str:
    return _fernet().decrypt(cipher.encode()).decode()


def _get_provider(provider_name: str, account_identifier: str, secret_key: str):
    if provider_name == "M-Pesa":
        from app.apps.verification.providers.mpesa import MpesaProvider
        return MpesaProvider(account_identifier, secret_key)
    if provider_name == "Selcom":
        from app.apps.verification.providers.selcom import SelcomProvider
        return SelcomProvider(account_identifier, secret_key)
    if provider_name == "AzamPay":
        from app.apps.verification.providers.azampay import AzamPayProvider
        return AzamPayProvider(account_identifier, secret_key)
    if provider_name == "Stripe":
        from app.apps.verification.providers.stripe import StripeProvider
        return StripeProvider(account_identifier, secret_key)
    raise ValueError(f"Unknown provider: {provider_name}")


class VerificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_startup(self, slug: str, founder: User) -> Startup | None:
        result = await self.db.exec(
            select(Startup).where(
                Startup.slug == slug,
                Startup.founder_id == founder.id,
                Startup.is_active == True,
            )
        )
        return result.first()

    async def connect_provider(
        self, startup_slug: str, founder: User, data: ConnectProviderIn
    ) -> VerificationStatusOut | None:
        startup = await self._get_startup(startup_slug, founder)
        if not startup:
            return None

        encrypted = encrypt_secret(data.secret_key)

        result = await self.db.exec(
            select(VerificationCredential).where(
                VerificationCredential.startup_id == startup.id
            )
        )
        cred = result.first()

        if cred:
            cred.provider = data.provider
            cred.account_identifier = data.account_identifier
            cred.encrypted_secret = encrypted
            cred.is_active = True
        else:
            cred = VerificationCredential(
                id=str(uuid.uuid4()),
                startup_id=startup.id,
                provider=data.provider,
                account_identifier=data.account_identifier,
                encrypted_secret=encrypted,
            )
        self.db.add(cred)

        provider = _get_provider(data.provider, data.account_identifier, data.secret_key)
        ok = await provider.verify_credentials()

        if ok:
            startup.is_verified = True
            startup.verification_source = data.provider
            startup.verified_at = datetime.utcnow()
            startup.tracked_since = startup.tracked_since or datetime.utcnow()
            cred.last_verified_at = datetime.utcnow()
            self.db.add(startup)

        return VerificationStatusOut(
            startup_id=startup.id,
            provider=data.provider,
            account_identifier=data.account_identifier,
            is_active=cred.is_active,
            last_verified_at=cred.last_verified_at.isoformat() if cred.last_verified_at else None,
            last_sync_status="success" if ok else "failed",
        )

    async def trigger_sync(
        self, startup_slug: str, founder: User
    ) -> VerificationStatusOut:
        startup = await self._get_startup(startup_slug, founder)
        if not startup:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Startup not found or not yours")

        result = await self.db.exec(
            select(VerificationCredential).where(
                VerificationCredential.startup_id == startup.id,
                VerificationCredential.is_active == True,
            )
        )
        cred = result.first()
        if not cred:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="No active verification credentials found")

        plain_secret = decrypt_secret(cred.encrypted_secret)
        provider = _get_provider(cred.provider, cred.account_identifier, plain_secret)

        since = date.today() - timedelta(days=30)
        until = date.today()
        sync_status = "success"

        try:
            records = await provider.fetch_revenue(since=since, until=until)
            for rec in records:
                snap = RevenueSnapshot(
                    id=str(uuid.uuid4()),
                    startup_id=startup.id,
                    snapshot_date=rec.snapshot_date,
                    revenue_usd=rec.revenue_usd,
                    charges_count=rec.charges_count,
                    currency_local=rec.currency_local,
                    revenue_local=rec.revenue_local,
                    exchange_rate=rec.exchange_rate,
                    source=cred.provider,
                )
                self.db.add(snap)

            if records:
                await self._update_startup_mrr(startup, records)

            cred.last_verified_at = datetime.utcnow()
            startup.last_synced_at = datetime.utcnow()
            self.db.add(cred)
            self.db.add(startup)
        except Exception:
            sync_status = "failed"

        return VerificationStatusOut(
            startup_id=startup.id,
            provider=cred.provider,
            account_identifier=cred.account_identifier,
            is_active=cred.is_active,
            last_verified_at=cred.last_verified_at.isoformat() if cred.last_verified_at else None,
            last_sync_status=sync_status,
        )

    async def _update_startup_mrr(self, startup: Startup, records) -> None:
        from app.apps.revenue.models import RevenueSnapshot
        from sqlmodel import func
        from datetime import date, timedelta

        last_30 = date.today() - timedelta(days=30)
        result = await self.db.exec(
            select(func.sum(RevenueSnapshot.revenue_usd)).where(
                RevenueSnapshot.startup_id == startup.id,
                RevenueSnapshot.snapshot_date >= last_30,
            )
        )
        mrr = result.one() or 0.0
        startup.mrr_usd = mrr
        startup.arr_usd = mrr * 12
        startup.last_30d_revenue_usd = mrr

    async def get_status(
        self, startup_slug: str, founder: User
    ) -> VerificationStatusOut | None:
        startup = await self._get_startup(startup_slug, founder)
        if not startup:
            return None

        result = await self.db.exec(
            select(VerificationCredential).where(
                VerificationCredential.startup_id == startup.id
            )
        )
        cred = result.first()
        if not cred:
            return None

        return VerificationStatusOut(
            startup_id=startup.id,
            provider=cred.provider,
            account_identifier=cred.account_identifier,
            is_active=cred.is_active,
            last_verified_at=cred.last_verified_at.isoformat() if cred.last_verified_at else None,
            last_sync_status="success" if cred.last_verified_at else "pending",
        )
