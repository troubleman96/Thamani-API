# app/apps/startups — Startup Profiles

The central domain of Thamani. Every startup on the platform is a `Startup` row. This app handles creation, listing (with filters), single-startup retrieval, updates, and soft deletion.

---

## Model — `Startup`

### Identity
| Field | Notes |
|-------|-------|
| `id` | UUID string |
| `slug` | Auto-generated from name, unique, URL-safe |
| `name` | Indexed for search |
| `tagline` | One-line description |
| `description` | Full description |
| `logo_emoji`, `logo_color`, `logo_url` | Visual identity |

### Classification
| Field | Notes |
|-------|-------|
| `category` | `StartupCategory` enum — SaaS, FinTech, AgriTech, etc. |
| `country` | `StartupCountry` enum — Tanzania, Kenya, Uganda, Rwanda, Ethiopia |
| `founded_date` | String e.g. `"September 2022"` |
| `tech_stack_frontend`, `tech_stack_backend` | JSON arrays |
| `marketing_channels`, `market_segments` | JSON arrays |

### Revenue (denormalized)
| Field | Notes |
|-------|-------|
| `mrr_usd` | Current MRR in USD — updated by verification sync worker |
| `arr_usd` | `mrr_usd * 12` |
| `last_30d_revenue_usd` | Rolling 30-day total |
| `active_subscriptions` | Count of active paying users |
| `mom_growth_pct` | Month-over-month growth — `null` until 2 months of data |

### Verification
| Field | Notes |
|-------|-------|
| `is_verified` | Set to `True` when provider credentials validate successfully |
| `verification_source` | `"M-Pesa"` / `"Selcom"` / `"AzamPay"` / `"Stripe"` |
| `tracked_since` | First sync date — used for leaderboard period filters |

---

## Slug generation

`_slugify(name)` lowercases, strips special chars, replaces spaces with `-`. On conflict, appends 8 random hex chars: `ziada-pos` → `ziada-pos-a3f2c1d9`.

---

## Service — `StartupService`

### `create_startup(founder, data)`
Generates slug, creates `Startup`, eagerly sets `startup.founder = founder` so the response can include founder data without a second query.

### `list_startups(params, ...)`
Builds a dynamic SQLModel `select()` with optional filters:
- `category`, `country` — exact enum match
- `is_verified` — boolean
- `min_mrr` / `max_mrr` — range on `mrr_usd`
- `search` — `ILIKE` on `name` and `tagline`
- `is_for_sale` — joins `Listing` table or excludes via subquery
- `sort_by` / `sort_dir` — any of `mrr_usd | created_at | mom_growth_pct | last_30d_revenue_usd`

Delegates to `paginate()` for count + offset queries.

### `_build_out(startup)` / `_build_list_out(startup)`
Converts ORM object to schema. Reads `startup.listing` relationship for `is_for_sale` and `listing` brief fields.

### Soft delete
`delete_startup` sets `is_active = False`. No row is ever deleted. All queries filter `is_active == True`.

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/startups` | — | Browse all startups (filters, pagination) |
| POST | `/api/v1/startups` | Bearer | Create a startup |
| GET | `/api/v1/startups/mine` | Bearer | My startups |
| GET | `/api/v1/startups/{slug}` | Optional | Single startup by slug |
| PATCH | `/api/v1/startups/{slug}` | Bearer (founder) | Update startup |
| DELETE | `/api/v1/startups/{slug}` | Bearer (founder) | Soft delete |

---

## Enums

```python
class StartupCategory(str, Enum):
    SAAS = "SaaS"
    AGRITECH = "AgriTech"
    FINTECH = "FinTech"
    HEALTHTECH = "HealthTech"
    EDUTECH = "EduTech"
    LOGISTICS = "Logistics"
    ECOMMERCE = "E-Commerce"
    REAL_ESTATE = "Real Estate"
    MOBILE_APPS = "Mobile Apps"
    AI_ML = "AI / ML"
    ENTERTAINMENT = "Entertainment"
    DEVELOPER_TOOLS = "Developer Tools"

class StartupCountry(str, Enum):
    TANZANIA = "Tanzania"
    KENYA = "Kenya"
    UGANDA = "Uganda"
    RWANDA = "Rwanda"
    ETHIOPIA = "Ethiopia"
```
