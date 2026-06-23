# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Thamani** is a FastAPI backend for East Africa's verified startup revenue marketplace. Every API endpoint returns a standard `ApiResponse[T]` envelope — no exceptions. Auth is Google OAuth2 and GitHub OAuth2 only (no email/password).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the development server (port 8050)
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8050 --reload

# Run all tests
pytest

# Run a single test file
pytest tests/test_auth.py -v

# Run a single test by name
pytest tests/test_auth.py::test_google_callback -v

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

## Architecture

### Apps-folder pattern
Each domain is a self-contained module under `app/apps/` (like Django apps in FastAPI):

```
app/
├── core/           # Cross-cutting: config, database, security, pagination, response, exceptions, dependencies
└── apps/
    ├── auth/       # Google + GitHub OAuth2, JWT issue/refresh/revoke
    ├── users/      # Founder profiles
    ├── startups/   # Startup CRUD + public listing
    ├── revenue/    # MRR snapshots (append-only)
    ├── verification/  # Payment processor credential storage + sync triggers
    ├── listings/   # Buy/sell marketplace
    ├── offers/     # Acquisition offers on listings
    ├── leaderboard/   # Redis-cached ranked leaderboard
    ├── saves/      # User-saved/bookmarked startups
    └── stats/      # Redis-cached platform-level analytics
```

### Core contracts

**ApiResponse envelope** (`app/core/response.py`) — every endpoint uses `ok()` or `fail()` helpers. Never return raw dicts or plain HTTP responses.

**Standard service pattern** — all business logic lives in class-based services (e.g. `StartupService(db)`), never inline in routers.

**Async everywhere** — all DB queries use `await db.exec(select(Model).where(...))` via SQLModel async session.

### Key rules
- Slugs are auto-generated from startup name + UUID suffix on conflict
- Soft deletes only — set `is_active = False`, never `DELETE FROM`
- Refresh tokens stored as SHA-256 hashes; raw token only returned on issue
- Provider credentials encrypted with AES-256 Fernet before storage
- Leaderboard cached in Redis TTL=300s; platform stats TTL=600s
- Revenue snapshots are append-only rows; MRR on `Startup` model is denormalized and updated after each sync
- All errors (including 404s) go through the exception handler and return `ApiResponse(success=False, ...)`

### API prefix
All routes are mounted under `/api/v1` in `main.py`.

### Port
This service runs on port **8050** (Camel VPS convention).

### Environment
Copy `.env.example` to `.env` before running. Required variables: `SECRET_KEY`, `DATABASE_URL`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_REDIRECT_URI`.
