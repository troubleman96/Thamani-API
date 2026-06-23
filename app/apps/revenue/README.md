# app/apps/revenue — Revenue History

Stores and serves the daily revenue snapshots that back each startup's verified revenue figures.

---

## Design principle: append-only

`RevenueSnapshot` rows are **never updated or deleted**. Each sync run writes new rows. This preserves a full audit trail and makes MoM growth calculations reliable. The denormalized `mrr_usd` / `arr_usd` fields on the `Startup` model are the fast-read summary; the snapshot table is the source of truth.

---

## Model — `RevenueSnapshot`

| Field | Notes |
|-------|-------|
| `startup_id` | FK to startups, indexed |
| `snapshot_date` | `date` — one row per calendar day per startup |
| `revenue_usd` | Total revenue that day in USD |
| `charges_count` | Number of individual transactions |
| `currency_local` | `"TZS"` / `"KES"` / `"USD"` |
| `revenue_local` | Revenue in local currency before conversion |
| `exchange_rate` | Local-to-USD rate at capture time |
| `source` | `"M-Pesa"` / `"Selcom"` / `"AzamPay"` / `"Stripe"` |
| `raw_payload` | JSON string of raw provider response — for debugging |

---

## Service — `RevenueService`

### `get_history(startup_slug, days)`
1. Looks up the startup by slug
2. Calculates `since = today - days`
3. Queries all snapshots in the date range, ordered by date ascending
4. Returns `RevenueHistoryOut` which includes the snapshot list plus the startup's denormalized `mrr_usd`, `arr_usd`, and `mom_growth_pct`

---

## Endpoint

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/revenue/{startup_slug}` | — | Revenue history (default 30 days, up to 365) |

### Query parameters
- `days` — integer, 7–365, default 30

### Response shape
```json
{
  "success": true,
  "message": "Revenue history retrieved successfully",
  "data": {
    "startup_id": "...",
    "startup_name": "Ziada POS",
    "verification_source": "M-Pesa",
    "tracked_since": "2024-01-15",
    "mrr_usd": 4200.00,
    "arr_usd": 50400.00,
    "mom_growth_pct": 12.5,
    "snapshots": [
      {
        "snapshot_date": "2024-05-01",
        "revenue_usd": 140.00,
        "charges_count": 23,
        "currency_local": "TZS",
        "revenue_local": 362600.00,
        "source": "M-Pesa"
      }
    ]
  }
}
```
