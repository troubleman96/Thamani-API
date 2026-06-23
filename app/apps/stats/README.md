# app/apps/stats — Platform Statistics

Returns aggregate metrics across the entire Thamani platform. Cached in Redis to avoid running heavy aggregate queries on every request.

---

## Caching strategy

Cache key: `platform:stats`
TTL: **600 seconds (10 minutes)**

The full `PlatformStatsOut` object is serialised to JSON and stored as a single Redis key. On a cache hit, the JSON is deserialised and returned directly with no DB query.

---

## Service — `StatsService`

Runs four queries in sequence:

1. **Totals** — `COUNT`, `SUM(is_verified)`, `SUM(mrr_usd)`, `SUM(arr_usd)` across all active startups
2. **Listing stats** — `COUNT` (for sale), `COUNT(sold_at)` (deals closed), `SUM(sold_price_usd)` (total deal value)
3. **By country** — GROUP BY `country`, returns count + MRR for each country
4. **By category** — GROUP BY `category`, returns count + MRR for each category
5. **Top growth** — TOP 5 startups by `mom_growth_pct` descending

---

## Output — `PlatformStatsOut`

```json
{
  "total_startups": 312,
  "verified_startups": 187,
  "total_mrr_usd": 1840000.00,
  "total_arr_usd": 22080000.00,
  "for_sale_count": 24,
  "total_deals_closed": 11,
  "total_deal_value_usd": 3250000.00,
  "by_country": {
    "Tanzania": { "count": 210, "mrr_usd": 1200000 },
    "Kenya": { "count": 72, "mrr_usd": 480000 }
  },
  "by_category": {
    "SaaS": { "count": 80, "mrr_usd": 720000 },
    "FinTech": { "count": 45, "mrr_usd": 380000 }
  },
  "top_growth_startups": [
    { "id": "...", "slug": "...", "name": "...", "mom_growth_pct": 42.0, "mrr_usd": 8200 }
  ]
}
```

---

## Endpoint

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/stats` | — | Platform aggregate stats (Redis-cached 10 min) |
