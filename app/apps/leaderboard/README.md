# app/apps/leaderboard — Startup Leaderboard

Ranks startups by revenue metrics. Results are cached in Redis to avoid running expensive aggregation queries on every page load.

---

## Caching strategy

Cache key format:
```
leaderboard:{metric}:{period}:{country}:{category}:{limit}
```

TTL: **300 seconds (5 minutes)**

On a cache hit, the JSON string is deserialised directly into `LeaderboardEntryOut` objects — no DB query. On a miss, the query runs, results are serialised to JSON, and the key is set with `SETEX`.

---

## Service — `LeaderboardService`

### `get_leaderboard(metric, period, country, category, limit)`

Builds a query against the `Startup` table joined to `User` (for founder info):

1. Filters `is_active=True`, `is_public=True`
2. **Period filter** — `last_30d` / `last_90d` filters on `startup.tracked_since`; `all_time` has no date filter
3. Optional `country` and `category` filters
4. Orders by the chosen metric (`mrr_usd` | `arr_usd` | `last_30d_revenue_usd`) descending
5. Limits to `limit` rows
6. Separately fetches active `Listing` startup IDs to populate `is_for_sale`
7. Assigns sequential `rank` starting at 1

---

## Output — `LeaderboardEntryOut`

Each entry includes:
- Rank, startup identity (id, slug, name, tagline, logos)
- Category, country
- Founder name and avatar
- All revenue metrics (MRR, ARR, 30d revenue, MoM growth)
- Active subscriptions
- Verification source
- `is_for_sale` flag

---

## Endpoint

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/leaderboard` | — | Ranked leaderboard (Redis-cached 5 min) |

### Query parameters
| Param | Default | Options |
|-------|---------|---------|
| `metric` | `mrr_usd` | `mrr_usd`, `arr_usd`, `last_30d_revenue_usd` |
| `period` | `all_time` | `all_time`, `last_90d`, `last_30d` |
| `country` | — | Any `StartupCountry` value |
| `category` | — | Any `StartupCategory` value |
| `limit` | 50 | 5–100 |
