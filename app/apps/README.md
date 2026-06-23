# app/apps — Domain Apps

Each subdirectory is a self-contained domain module — like Django apps, but in FastAPI. Each app owns its models, schemas, service layer, and router. Apps may import from `app/core/` and from each other's **models only** (for relationships), but business logic stays within the owning app.

---

## Apps at a glance

| App | Purpose | Key model(s) |
|-----|---------|--------------|
| [`auth/`](auth/README.md) | OAuth2 login, JWT issue/refresh/revoke | `OAuthAccount`, `RefreshToken` |
| [`users/`](users/README.md) | Founder profiles | `User` |
| [`startups/`](startups/README.md) | Startup CRUD + public listing | `Startup` |
| [`revenue/`](revenue/README.md) | Daily revenue snapshots | `RevenueSnapshot` |
| [`verification/`](verification/README.md) | Payment processor credentials + sync | `VerificationCredential` |
| [`listings/`](listings/README.md) | For-sale marketplace listings | `Listing` |
| [`offers/`](offers/README.md) | Acquisition offers on listings | `Offer` |
| [`saves/`](saves/README.md) | Bookmarked startups | `SavedStartup` |
| [`leaderboard/`](leaderboard/README.md) | Redis-cached ranked leaderboard | — |
| [`stats/`](stats/README.md) | Redis-cached platform analytics | — |

---

## Conventions every app follows

### File layout
```
app_name/
├── __init__.py
├── models.py    # SQLModel table models
├── schemas.py   # Pydantic input/output schemas
├── service.py   # Class-based service (all DB logic lives here)
└── router.py    # FastAPI router (thin — delegates to service)
```

Apps that have no DB table (`leaderboard`, `stats`) omit `models.py`. Apps with sub-providers have a `providers/` subpackage.

### Service pattern
```python
class FooService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def do_thing(self, ...) -> FooOut | None:
        ...
```

Services are instantiated per-request inside the router function. Never use module-level service instances.

### Response pattern
Every router function returns `ok(data=..., message="...")` or `fail(message=..., errors=[...])`. Raw dicts and `JSONResponse` are not used.

### Auth guards
- `Depends(get_current_user)` — requires valid Bearer token, raises 401 otherwise
- `Depends(get_optional_user)` — returns `User | None`, never raises
