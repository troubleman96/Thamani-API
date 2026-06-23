# app/core — Cross-Cutting Infrastructure

All modules here are shared across every app. Nothing in `core/` imports from `apps/`.

---

## Modules

### `config.py`
Loads all environment variables via `pydantic-settings`. The singleton `settings` object is imported directly — never instantiate `Settings` yourself. Adding a new env var means adding a typed field here and a matching line to `.env.example`.

### `database.py`
Creates an async SQLAlchemy engine and `AsyncSessionLocal` session factory. The `get_db()` dependency yields a session, auto-commits on success, and rolls back on any exception. `create_db_and_tables()` is called once at startup via the FastAPI lifespan.

### `redis.py`
Lazy-initialised async Redis client. Call `await get_redis()` anywhere — it returns the same connection pool on every call. `close_redis()` is called in the lifespan shutdown hook.

### `response.py`
Defines the `ApiResponse[T]` generic envelope and two helpers:

```python
ok(data=..., message="...", meta={...})   # success=True
fail(message="...", errors=[...])          # success=False
```

Every router must use one of these — never return a raw dict or a plain `JSONResponse`.

### `exceptions.py`
Two global exception handlers registered in `main.py`:
- `http_exception_handler` — wraps `HTTPException` into `ApiResponse`
- `validation_exception_handler` — wraps Pydantic `RequestValidationError` into `ApiResponse`

This guarantees that even 404s and 422s return the standard envelope.

### `security.py`
JWT helpers using `PyJWT`:
- `create_access_token(user_id, extra={})` — short-lived (default 60 min), type=`"access"`
- `create_refresh_token(user_id)` — long-lived (default 30 days), type=`"refresh"`
- `decode_token(token)` — raises `jwt.ExpiredSignatureError` or `jwt.InvalidTokenError` on failure

**Never store or log raw refresh tokens.** They are hashed with SHA-256 before hitting the DB.

### `dependencies.py`
FastAPI dependency functions:
- `get_current_user` — extracts Bearer token, validates it, returns the `User` ORM object. Raises 401 on any failure.
- `get_optional_user` — same but returns `None` instead of raising if no token is present. Used on public endpoints that personalise output when logged in.

### `pagination.py`
- `PaginationParams` — Pydantic model holding `page` and `per_page` (validated query params)
- `PaginationMeta` — returned in the `meta` field of every list response
- `paginate(db, query, params)` — runs a count query then a paginated query, returns `(items, meta)`

### `middleware.py`
`RequestLoggingMiddleware` — logs `METHOD /path STATUS Xms` for every request using Python's standard `logging` module.
