# tests — Test Suite

Uses `pytest-asyncio` with an async HTTPX client against the full FastAPI app (ASGI transport — no live server needed).

---

## Setup

Tests require a separate PostgreSQL database:

```bash
createdb thamani_test
```

The test database URL is hardcoded in `conftest.py`:
```
postgresql+asyncpg://camel:password@localhost:5432/thamani_test
```

Run all tests:
```bash
pytest
```

Run a single file:
```bash
pytest tests/test_auth.py -v
```

Run a single test:
```bash
pytest tests/test_startups.py::test_list_startups_public -v
```

---

## `conftest.py`

### Fixtures

**`setup_db`** (session-scoped, autouse)
Creates all tables before the test session, drops them after. Runs once per `pytest` invocation.

**`db`** (function-scoped)
Yields an `AsyncSession` and rolls back after each test — tests are isolated from each other with no cleanup code needed.

**`client`** (function-scoped)
Overrides the `get_db` FastAPI dependency to inject the test session. Creates an `AsyncClient` with `ASGITransport` — no network calls, no live port.

---

## Test files

| File | Coverage area |
|------|---------------|
| `test_auth.py` | OAuth login redirects, unauthenticated /me, invalid refresh token |
| `test_startups.py` | Public list, nonexistent slug returns `success=false`, create requires auth |
| `test_listings.py` | Public browse, create requires auth, offer requires auth |
| `test_revenue.py` | Nonexistent startup returns `success=false`, health check, ping |

---

## Adding tests for authenticated flows

Override `get_current_user` in the dependency overrides to inject a fake user:

```python
from app.core.dependencies import get_current_user
from app.apps.users.models import User

fake_user = User(id="test-id", email="test@example.com", full_name="Test", primary_provider="google")

@pytest_asyncio.fixture
async def auth_client(db):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```
