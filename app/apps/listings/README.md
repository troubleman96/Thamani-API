# app/apps/listings — Marketplace Listings

When a founder wants to sell their startup, they create a `Listing`. Only verified startups can be listed for sale.

---

## Model — `Listing`

| Field | Notes |
|-------|-------|
| `startup_id` | FK to startups, unique — one listing per startup |
| `asking_price_usd` | Set by the founder |
| `revenue_multiple` | Auto-calculated: `asking_price / (mrr * 12)` |
| `ttm_profit_usd` | Optional trailing-12-month profit |
| `founder_message` | Why the founder is selling |
| `affiliate_earnings_usd` | Earnings from Thamani affiliate program |
| `offers_received` | Denormalized count, incremented on each offer |
| `buyer_views` | Incremented each time a buyer views the listing detail |
| `is_active` | False when delisted or sold |
| `sold_at`, `sold_price_usd` | Set when an offer is accepted |

---

## Revenue multiple calculation

When creating or updating a listing, `revenue_multiple` is computed automatically:

```
revenue_multiple = asking_price_usd / (startup.mrr_usd * 12)
```

If `mrr_usd` is 0 (unverified startup), the multiple is set to `0.0`.

---

## Service — `ListingService`

### `create(startup_slug, founder, data)`
- Requires `startup.is_verified == True` — unverified startups cannot be listed
- If a listing already exists for this startup (even inactive), it is reactivated and updated rather than a duplicate row being created
- Calculates `revenue_multiple` from the startup's current `mrr_usd`

### `list_active(params, ...)`
Joins `Startup` to allow filtering by category, country, and MRR range. Also accepts `min_multiple`/`max_multiple` filters directly on the listing's `revenue_multiple`.

### `delist(startup_slug, founder)`
Sets `is_active = False`. The listing row is preserved for historical reference.

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/listings` | — | Browse active listings |
| POST | `/api/v1/listings/{startup_slug}` | Bearer (founder, verified) | List startup for sale |
| PATCH | `/api/v1/listings/{startup_slug}` | Bearer (founder) | Update listing price/message |
| DELETE | `/api/v1/listings/{startup_slug}` | Bearer (founder) | Delist (remove from marketplace) |

### Browse filters
`category`, `country`, `min_mrr`, `max_mrr`, `min_multiple`, `max_multiple`, `sort_by` (`buyer_views` | `created_at` | `asking_price_usd` | `revenue_multiple`)
