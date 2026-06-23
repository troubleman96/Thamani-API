# app/apps/verification — Revenue Verification

Manages the connection between a startup and its payment processor. This is what makes Thamani's revenue figures trustworthy — every verified startup has a live API connection to its payment processor.

---

## Security model

1. The founder submits their payment provider API credentials via `POST /verification/{slug}/connect`
2. The `secret_key` field is **immediately encrypted** with AES-256 Fernet before any DB write
3. The raw secret is never logged, stored in plaintext, or returned in any response
4. On sync, the ciphertext is decrypted in memory, used to fetch revenue, then discarded
5. The encryption key is derived from the first 32 bytes of `SECRET_KEY` in `.env`

```python
def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32, b"0"))
    return Fernet(key)
```

---

## Model — `VerificationCredential`

One row per startup (enforced by `unique=True` on `startup_id`). Reconnecting a provider overwrites the existing row rather than creating a new one.

| Field | Notes |
|-------|-------|
| `startup_id` | FK to startups, unique |
| `provider` | `"M-Pesa"` / `"Selcom"` / `"AzamPay"` / `"Stripe"` |
| `account_identifier` | Shortcode / account ID / publishable key — safe to store plain |
| `encrypted_secret` | AES-256 Fernet ciphertext of the API key/secret |
| `last_verified_at` | Updated on each successful credential test |

---

## Providers (`providers/`)

All providers implement `BaseRevenueProvider` (abstract base class):

```python
class BaseRevenueProvider(ABC):
    async def fetch_revenue(self, since: date, until: date) -> list[RevenueRecord]: ...
    async def verify_credentials(self) -> bool: ...
```

### `MpesaProvider`
Uses Safaricom Daraja OAuth2 (`client_credentials`) to get an access token. Credential verification = successful token fetch. Revenue fetch uses Daraja transaction query APIs.

### `SelcomProvider`
Signs requests with HMAC-SHA256 using the API secret. The signature goes in the `Authorization` header as `SELCOM {api_key}:{base64_signature}`. Credential verification = successful order-list request.

### `AzamPayProvider`
Gets a JWT token from AzamPay's `GenerateToken` endpoint using `clientId` + `clientSecret`. Credential verification = successful token generation.

### `StripeProvider`
Uses Bearer auth with the secret key. Credential verification = `GET /v1/balance` returns 200. Revenue fetch paginates `GET /v1/charges` with `created[gte]` and `created[lte]` filters, then rolls up charges by day.

---

## Service — `VerificationService`

### `connect_provider(startup_slug, founder, data)`
1. Validates startup ownership
2. Encrypts `data.secret_key`
3. Upserts `VerificationCredential`
4. Calls `provider.verify_credentials()` to test live connectivity
5. On success: marks startup `is_verified=True`, sets `verification_source`, `verified_at`, `tracked_since`

### `trigger_sync(startup_slug, founder)`
1. Decrypts stored secret
2. Fetches last 30 days of revenue via `provider.fetch_revenue()`
3. Writes new `RevenueSnapshot` rows (append-only)
4. Calls `_update_startup_mrr()` to recalculate and persist `mrr_usd`, `arr_usd`, `last_30d_revenue_usd`

### `_update_startup_mrr(startup, records)`
SUMs `revenue_usd` from snapshots in the last 30 days and writes back to the `Startup` row.

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/verification/{slug}/connect` | Bearer (founder) | Connect and verify provider credentials |
| POST | `/api/v1/verification/{slug}/sync` | Bearer (founder) | Trigger manual revenue sync |
| GET | `/api/v1/verification/{slug}/status` | Bearer (founder) | Check current verification status |
