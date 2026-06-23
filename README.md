# Thamani API

**East Africa's verified startup revenue marketplace.**

Thamani lets startup founders connect their payment processors (M-Pesa, Selcom, AzamPay, Stripe), automatically verify and display their live revenue, and optionally list their company for acquisition. Investors and buyers browse verified revenue metrics, submit offers, and track deal progress — all through this API.

Built by **CamelTech**, Dar es Salaam.

---

## Table of contents

1. [Tech stack](#tech-stack)
2. [Architecture overview](#architecture-overview)
3. [Project structure](#project-structure)
4. [Quick start](#quick-start)
5. [Environment variables](#environment-variables)
6. [Running the server](#running-the-server)
7. [Database migrations](#database-migrations)
8. [API reference](#api-reference)
9. [Authentication flow](#authentication-flow)
10. [Revenue verification flow](#revenue-verification-flow)
11. [Marketplace flow](#marketplace-flow)
12. [API response envelope](#api-response-envelope)
13. [Pagination](#pagination)
14. [Redis caching](#redis-caching)
15. [Security model](#security-model)
16. [Testing](#testing)
17. [Data model diagram](#data-model-diagram)

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.115 |
| ORM | SQLModel 0.0.21 (SQLAlchemy 2.0 async) |
| Database | PostgreSQL (async via `asyncpg`) |
| Cache | Redis (async via `redis[asyncio]`) |
| Migrations | Alembic (async-compatible) |
| Auth | OAuth2 (Google + GitHub) + PyJWT |
| Encryption | `cryptography` Fernet (AES-256) |
| HTTP client | httpx (async) |
| Validation | Pydantic v2 |
| Server | Uvicorn |
| Tests | pytest + pytest-asyncio + HTTPX ASGI transport |

---

## Architecture overview

```
                          ┌─────────────────────────────────────────┐
                          │              main.py                     │
                          │  FastAPI app factory                     │
                          │  - CORS middleware                       │
                          │  - Request logging middleware            │
                          │  - Global exception handlers             │
                          │  - All routers mounted at /api/v1        │
                          │  - Lifespan: DB init + Redis cleanup     │
                          └────────────────┬────────────────────────┘
                                           │
                 ┌─────────────────────────┼──────────────────────────┐
                 │                         │                          │
          ┌──────▼──────┐          ┌───────▼──────┐          ┌───────▼──────┐
          │  app/core/  │          │  app/apps/   │          │   alembic/   │
          │             │          │              │          │              │
          │ config      │          │ auth         │          │ env.py       │
          │ database    │          │ users        │          │ versions/    │
          │ redis       │          │ startups     │          └──────────────┘
          │ response    │          │ revenue      │
          │ exceptions  │◄─────────│ verification │
          │ security    │          │ listings     │
          │ dependencies│          │ offers       │
          │ pagination  │          │ saves        │
          │ middleware  │          │ leaderboard  │
          └─────────────┘          │ stats        │
                                   └──────────────┘
```

### Apps-folder pattern

Each domain in `app/apps/` is self-contained — it has its own models, schemas, service layer, and router. This is intentional: you can read any single app's folder and understand that domain without cross-referencing other apps. Business logic never lives in routers — routers call services, services contain all logic.

```
router.py  →  service.py  →  models.py
   thin           fat          ORM
```

---

## Project structure

```
thamani-api/
│
├── main.py                          # FastAPI app factory + router registration
├── requirements.txt
├── .env.example                     # Copy to .env and fill in secrets
├── alembic.ini
├── CLAUDE.md                        # AI coding assistant context
│
├── alembic/
│   ├── env.py                       # Async-compatible migration runner
│   └── versions/                    # Auto-generated migration files
│
├── app/
│   ├── core/                        # Shared infrastructure (no domain knowledge)
│   │   ├── config.py                # Settings loaded from .env via pydantic-settings
│   │   ├── database.py              # Async engine + session factory + get_db dependency
│   │   ├── redis.py                 # Lazy async Redis client
│   │   ├── response.py              # ApiResponse[T] envelope + ok() / fail() helpers
│   │   ├── exceptions.py            # Global HTTP + validation exception handlers
│   │   ├── security.py              # JWT create + decode
│   │   ├── dependencies.py          # get_current_user / get_optional_user
│   │   ├── pagination.py            # PaginationParams + paginate() helper
│   │   └── middleware.py            # Request logging middleware
│   │
│   └── apps/
│       ├── auth/                    # Google + GitHub OAuth2, JWT lifecycle
│       │   └── providers/           # google.py, github.py
│       ├── users/                   # Founder profile CRUD
│       ├── startups/                # Startup CRUD + public marketplace browse
│       ├── revenue/                 # Daily revenue snapshots (append-only)
│       ├── verification/            # Payment processor connections + sync
│       │   └── providers/           # base.py, mpesa.py, selcom.py, azampay.py, stripe.py
│       ├── listings/                # For-sale marketplace listings
│       ├── offers/                  # Acquisition offers on listings
│       ├── saves/                   # User-bookmarked startups
│       ├── leaderboard/             # Redis-cached ranked leaderboard
│       └── stats/                   # Redis-cached platform analytics
│
└── tests/
    ├── conftest.py                  # Test DB + async HTTPX client fixtures
    ├── test_auth.py
    ├── test_startups.py
    ├── test_listings.py
    └── test_revenue.py
```

---

## Quick start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+

### 1. Clone and install

```bash
git clone git@github.com:troubleman96/Thamani-API.git
cd Thamani-API
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` — at minimum you need:

```env
SECRET_KEY=<64+ character random string>
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/thamani_db
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8050/api/v1/auth/google/callback
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITHUB_REDIRECT_URI=http://localhost:8050/api/v1/auth/github/callback
```

### 3. Create the database

```bash
createdb thamani_db
```

### 4. Run migrations (or let the server auto-create tables)

```bash
alembic upgrade head
```

Or just start the server — on first run the `lifespan` hook calls `create_db_and_tables()` which creates all tables from SQLModel metadata.

### 5. Start the server

```bash
python main.py
```

The server starts on `http://0.0.0.0:8050`. In development (`DEBUG=true`), interactive docs are available at:
- Swagger UI: `http://localhost:8050/docs`
- ReDoc: `http://localhost:8050/redoc`

---

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ | — | Min 64 chars. Used for JWT signing AND Fernet encryption key derivation. |
| `DATABASE_URL` | ✅ | — | PostgreSQL async URL: `postgresql+asyncpg://...` |
| `REDIS_URL` | | `redis://localhost:6379/0` | Redis connection URL |
| `APP_ENV` | | `development` | Environment name |
| `DEBUG` | | `false` | Enables `/docs`, `/redoc`, and SQL echo |
| `APP_PORT` | | `8050` | Uvicorn port |
| `ALLOWED_ORIGINS` | | `http://localhost:5173` | Comma-separated CORS origins |
| `FRONTEND_URL` | | `http://localhost:5173` | OAuth callback redirect target |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | | `60` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | | `30` | Refresh token lifetime |
| `GOOGLE_CLIENT_ID` | ✅ | — | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | ✅ | — | From Google Cloud Console |
| `GOOGLE_REDIRECT_URI` | ✅ | — | Must match registered OAuth callback |
| `GITHUB_CLIENT_ID` | ✅ | — | From GitHub Developer Settings |
| `GITHUB_CLIENT_SECRET` | ✅ | — | From GitHub Developer Settings |
| `GITHUB_REDIRECT_URI` | ✅ | — | Must match registered OAuth callback |
| `MPESA_CONSUMER_KEY` | | — | Safaricom Daraja API |
| `MPESA_CONSUMER_SECRET` | | — | Safaricom Daraja API |
| `MPESA_SHORTCODE` | | — | M-Pesa till/paybill number |
| `MPESA_ENV` | | `sandbox` | `sandbox` or `production` |
| `SELCOM_API_KEY` | | — | Selcom API key |
| `SELCOM_API_SECRET` | | — | Selcom API secret (used for HMAC signing) |
| `SELCOM_VENDOR` | | — | Selcom vendor ID |
| `AZAMPAY_APP_NAME` | | — | AzamPay app registration name |
| `AZAMPAY_CLIENT_ID` | | — | AzamPay client ID |
| `AZAMPAY_CLIENT_SECRET` | | — | AzamPay client secret |
| `AZAMPAY_ENV` | | `sandbox` | `sandbox` or `production` |
| `STRIPE_SECRET_KEY` | | — | Stripe secret key (`sk_live_...` or `sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | | — | Stripe webhook signing secret |
| `RATE_LIMIT_PER_MINUTE` | | `60` | Max requests per IP per minute |

---

## Running the server

```bash
# Development (auto-reload)
DEBUG=true python main.py

# Production (Uvicorn directly)
uvicorn main:app --host 0.0.0.0 --port 8050 --workers 4

# Production (Gunicorn + Uvicorn workers)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8050
```

---

## Database migrations

```bash
# Generate a new migration after modifying models
alembic revision --autogenerate -m "describe the change"

# Apply all pending migrations
alembic upgrade head

# Roll back the most recent migration
alembic downgrade -1

# Show current migration state
alembic current

# Show full history
alembic history --verbose
```

When adding a new SQLModel table model, also add its import to `alembic/env.py` so autogenerate can detect it.

---

## API reference

All endpoints are prefixed with `/api/v1`.

### Health

```
GET  /           → {"success": true, "message": "Thamani API is running", "version": "1.0.0"}
GET  /ping       → {"ping": "pong"}
```

### Authentication

```
GET  /auth/google/login          Redirect to Google OAuth2 consent screen
GET  /auth/google/callback       Handle Google callback → redirect to frontend with tokens
GET  /auth/github/login          Redirect to GitHub OAuth2 consent screen
GET  /auth/github/callback       Handle GitHub callback → redirect to frontend with tokens
POST /auth/refresh               Body: {refresh_token} → new access + refresh token pair
POST /auth/logout                Body: {refresh_token} → revoke token
GET  /auth/me              🔒    Current user (id, email, full_name, provider, is_verified)
```

### Users

```
GET   /users/me            🔒    My full private profile (includes email + provider)
PATCH /users/me            🔒    Update profile (full_name, bio, twitter, website, country)
GET   /users/{user_id}           Any user's public profile (no email)
```

### Startups

```
GET    /startups                 Browse all public startups (see filters below)
POST   /startups           🔒    Create a startup
GET    /startups/mine      🔒    My startups
GET    /startups/{slug}          Single startup by slug
PATCH  /startups/{slug}    🔒    Update startup (founder only)
DELETE /startups/{slug}    🔒    Soft delete (founder only)
```

**Browse filters** (`GET /startups`):

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Page number (default 1) |
| `per_page` | int | Items per page (default 20, max 100) |
| `category` | enum | SaaS, FinTech, AgriTech, etc. |
| `country` | enum | Tanzania, Kenya, Uganda, Rwanda, Ethiopia |
| `is_for_sale` | bool | Filter to listed/unlisted startups |
| `is_verified` | bool | Filter to verified/unverified |
| `min_mrr` | float | Minimum MRR in USD |
| `max_mrr` | float | Maximum MRR in USD |
| `search` | string | ILIKE search on name and tagline |
| `sort_by` | string | `mrr_usd` \| `created_at` \| `mom_growth_pct` \| `last_30d_revenue_usd` |
| `sort_dir` | string | `asc` \| `desc` (default `desc`) |

### Revenue

```
GET  /revenue/{startup_slug}     Revenue history (query param: days=30, range 7–365)
```

### Verification

```
POST /verification/{slug}/connect  🔒  Connect a payment provider (M-Pesa/Selcom/AzamPay/Stripe)
POST /verification/{slug}/sync     🔒  Trigger manual revenue sync
GET  /verification/{slug}/status   🔒  Check verification status
```

### Listings (Marketplace)

```
GET    /listings                   Browse active for-sale listings
POST   /listings/{startup_slug}    🔒  List startup for sale (must be verified founder)
PATCH  /listings/{startup_slug}    🔒  Update asking price / founder message
DELETE /listings/{startup_slug}    🔒  Delist startup (soft remove)
```

**Browse filters** (`GET /listings`):

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by startup category |
| `country` | string | Filter by startup country |
| `min_mrr` / `max_mrr` | float | MRR range |
| `min_multiple` / `max_multiple` | float | Revenue multiple range |
| `sort_by` | string | `buyer_views` \| `created_at` \| `asking_price_usd` \| `revenue_multiple` |

### Offers

```
POST  /offers                      🔒  Submit an acquisition offer
GET   /offers/received             🔒  All offers on my listings
PATCH /offers/{id}/accept          🔒  Accept an offer (marks listing as sold)
PATCH /offers/{id}/reject          🔒  Reject an offer
```

### Leaderboard

```
GET  /leaderboard                  Ranked startup leaderboard (Redis-cached 5 min)
```

| Parameter | Default | Options |
|-----------|---------|---------|
| `metric` | `mrr_usd` | `mrr_usd`, `arr_usd`, `last_30d_revenue_usd` |
| `period` | `all_time` | `all_time`, `last_90d`, `last_30d` |
| `country` | — | Any StartupCountry value |
| `category` | — | Any StartupCategory value |
| `limit` | 50 | 5–100 |

### Saves

```
POST /saves/{startup_slug}   🔒   Toggle save/unsave (returns current state)
GET  /saves                  🔒   My saved startups
```

### Platform Stats

```
GET  /stats                       Aggregate platform stats (Redis-cached 10 min)
```

> 🔒 = Requires `Authorization: Bearer <access_token>` header

---

## Authentication flow

Thamani uses **OAuth2 only** — no email/password registration. Here is the complete flow from the frontend's perspective:

### Step 1 — Initiate login
```javascript
// Redirect the browser directly to the API login URL
window.location.href = 'http://localhost:8050/api/v1/auth/google/login'
// or
window.location.href = 'http://localhost:8050/api/v1/auth/github/login'
```

### Step 2 — User grants consent
The browser is redirected to Google/GitHub, the user approves, and the provider redirects back to the API callback URL.

### Step 3 — Receive tokens
After the callback is processed, the API redirects to your `FRONTEND_URL`:
```
http://localhost:5173/auth/callback?access_token=eyJ...&refresh_token=eyJ...
```

Store both tokens securely (e.g. `localStorage` for SPAs, `httpOnly` cookie in SSR).

### Step 4 — Authenticate requests
```http
GET /api/v1/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Step 5 — Refresh when expired
Access tokens expire in 60 minutes (configurable). When you receive a 401, call refresh:
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{"refresh_token": "eyJ..."}
```

Response:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

**Token rotation**: the old refresh token is revoked on each refresh call. Always store the new refresh token.

### Step 6 — Logout
```http
POST /api/v1/auth/logout
Content-Type: application/json

{"refresh_token": "eyJ..."}
```

---

## Revenue verification flow

This is the core feature that makes Thamani trustworthy — startups prove their revenue by connecting a live payment processor account.

```
Founder                    Thamani API                   Payment Processor
   │                           │                                │
   │  POST /verification/      │                               │
   │  {slug}/connect           │                               │
   │  {provider, account_id,   │                               │
   │   secret_key}             │                               │
   │ ─────────────────────────>│                               │
   │                           │  Encrypt secret_key (AES-256) │
   │                           │  Upsert credential row        │
   │                           │  Test credentials live ──────>│
   │                           │                        ← OK   │
   │                           │  Mark startup is_verified=True│
   │ <─────────────────────────│                               │
   │  {status: "success"}      │                               │
   │                           │                               │
   │  POST /verification/      │                               │
   │  {slug}/sync              │                               │
   │ ─────────────────────────>│                               │
   │                           │  Decrypt secret in memory     │
   │                           │  Fetch 30d revenue ──────────>│
   │                           │          ← daily records      │
   │                           │  Write RevenueSnapshot rows   │
   │                           │  Update startup.mrr_usd       │
   │ <─────────────────────────│                               │
   │  {last_sync_status: "ok"} │                               │
```

### Supported providers

| Provider | Region | Auth method |
|----------|--------|-------------|
| M-Pesa (Daraja) | Tanzania, Kenya | OAuth2 client credentials |
| Selcom | Tanzania | HMAC-SHA256 signed headers |
| AzamPay | Tanzania | JWT token (clientId + clientSecret) |
| Stripe | Global | Bearer API key |

---

## Marketplace flow

```
1. Founder connects payment processor → startup becomes "verified"
2. Founder creates listing (POST /listings/{slug})
   - Only verified startups can be listed
   - Revenue multiple is auto-calculated: asking_price / (mrr * 12)
3. Buyer browses listings (GET /listings)
   - Filters by category, country, MRR range, multiple range
4. Buyer submits offer (POST /offers)
   - offer.status = "pending"
   - listing.offers_received incremented
5. Founder reviews offers (GET /offers/received)
6a. Founder accepts (PATCH /offers/{id}/accept)
    - offer.status = "accepted"
    - listing.sold_at, listing.sold_price_usd set
    - listing.is_active = false
6b. Founder rejects (PATCH /offers/{id}/reject)
    - offer.status = "rejected"
    - listing remains active
```

---

## API response envelope

**Every single endpoint** returns this structure:

```typescript
interface ApiResponse<T> {
  success: boolean
  message: string
  data: T | null
  errors: string[] | null
  meta: Record<string, any> | null  // used for pagination info on list endpoints
}
```

**Success example:**
```json
{
  "success": true,
  "message": "Startups retrieved successfully",
  "data": [...],
  "errors": null,
  "meta": {
    "total": 312,
    "page": 1,
    "per_page": 20,
    "pages": 16,
    "has_next": true,
    "has_prev": false
  }
}
```

**Error example:**
```json
{
  "success": false,
  "message": "Startup not found",
  "data": null,
  "errors": ["No startup with slug 'nonexistent-startup' exists"],
  "meta": null
}
```

Even HTTP 404, 401, and 422 responses use this envelope — they are caught by the global exception handlers in `app/core/exceptions.py`.

---

## Pagination

List endpoints that return multiple items include pagination metadata in the `meta` field:

```json
"meta": {
  "total": 312,
  "page": 2,
  "per_page": 20,
  "pages": 16,
  "has_next": true,
  "has_prev": true
}
```

Query parameters: `?page=1&per_page=20` (per_page max 100).

---

## Redis caching

Two endpoints cache their results in Redis to avoid running expensive aggregate queries on each request:

| Endpoint | Cache key pattern | TTL |
|----------|------------------|-----|
| `GET /leaderboard` | `leaderboard:{metric}:{period}:{country}:{category}:{limit}` | 300s (5 min) |
| `GET /stats` | `platform:stats` | 600s (10 min) |

Cache is populated on the first request after expiry. The cache key for leaderboard includes all filter parameters so different filter combinations are cached independently.

---

## Security model

### Authentication
- **No email/password** — only Google and GitHub OAuth2
- Access tokens are short-lived JWTs (HS256, default 60 min)
- Refresh tokens are long-lived JWTs (default 30 days) stored as SHA-256 hashes in the DB
- Raw refresh tokens are never stored and never logged
- Token rotation: every refresh call revokes the old token and issues a new pair

### Credential encryption
Payment processor API secrets are encrypted with **AES-256 Fernet** before any DB write:

```python
key = base64.urlsafe_b64encode(SECRET_KEY[:32].encode().ljust(32, b"0"))
fernet = Fernet(key)
encrypted = fernet.encrypt(raw_secret.encode())
```

The `encrypted_secret` field is never returned in any API response. Decryption happens in memory during sync and is not persisted.

### Ownership guards
All mutating operations verify ownership at the service layer before touching data:
- Startup updates/deletes: `founder_id == current_user.id`
- Listing create/update/delete: startup `founder_id == current_user.id`
- Offer accept/reject: traced via JOIN chain to `startup.founder_id == current_user.id`
- Verification connect/sync/status: startup `founder_id == current_user.id`

### Soft deletes
No data is ever hard-deleted. All models use an `is_active` flag. Queries always filter `is_active == True`.

---

## Testing

### Setup test database
```bash
createdb thamani_test
```

### Run tests
```bash
# All tests
pytest

# Single file
pytest tests/test_auth.py -v

# Single test
pytest tests/test_auth.py::test_google_login_redirects -v

# With coverage
pytest --cov=app tests/
```

Tests use ASGI transport — no network calls, no live server, no Redis needed. The test session creates all tables, runs tests in isolated transactions (auto-rollback), and drops all tables on exit.

See [`tests/README.md`](tests/README.md) for how to write tests for authenticated endpoints.

---

## Data model diagram

```
┌──────────┐         ┌───────────────┐
│   User   │ 1     * │  OAuthAccount │
│──────────│◄────────│───────────────│
│ id       │         │ provider      │
│ email    │         │ provider_uid  │
│ full_name│         │ access_token  │
│ country  │ 1     * └───────────────┘
│ is_admin │
└────┬─────┘         ┌───────────────┐
     │               │ RefreshToken  │
     │ 1           * │───────────────│
     │◄──────────────│ token_hash    │
     │               │ revoked       │
     │               └───────────────┘
     │ 1           *
     ▼
┌──────────────────────────┐      ┌──────────────────────────┐
│         Startup          │ 1  1 │  VerificationCredential  │
│──────────────────────────│◄─────│──────────────────────────│
│ slug                     │      │ provider                 │
│ category / country       │      │ encrypted_secret         │
│ mrr_usd / arr_usd        │      │ last_verified_at         │
│ is_verified              │      └──────────────────────────┘
│ verification_source      │
└──────┬───────────────────┘
       │
       ├──────────────────────────── 1:* ──► RevenueSnapshot
       │                                     (append-only, daily)
       │
       └──────────────────────────── 1:1 ──► Listing
                                              │
                                              └── 1:* ──► Offer
                                                          (buyer_id → User)

┌──────────────────┐
│  SavedStartup    │   (user_id → User, startup_id → Startup)
└──────────────────┘
```

---

## Deployment notes

- Port **8050** is the CamelTech VPS convention for this service
- Set `DEBUG=false` in production — this disables `/docs` and `/redoc` and turns off SQL echo
- Use at least 4 Uvicorn workers in production: `--workers 4`
- Rotate `SECRET_KEY` only with a migration plan — changing it invalidates all JWTs and Fernet ciphertexts simultaneously
- Redis is required in production for the leaderboard and stats endpoints to function
- The `ALLOWED_ORIGINS` env var must include your frontend domain in production

---

*Thamani — making East African startup revenue transparent.*
