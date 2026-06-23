# app/apps/saves — Saved Startups

Allows authenticated users to bookmark startups they're interested in. The save/unsave action is a single toggle endpoint.

---

## Model — `SavedStartup`

A simple join table:

| Field | Notes |
|-------|-------|
| `user_id` | FK to users, indexed |
| `startup_id` | FK to startups, indexed |
| `created_at` | Used to order the saved list by recency |

There is intentionally no unique constraint enforced at the DB level — `toggle()` handles idempotency in the service layer by checking for an existing row before deciding whether to insert or delete.

---

## Service — `SavesService`

### `toggle(user, startup_slug)`
1. Looks up the startup by slug (must be active)
2. Looks for an existing `SavedStartup` row for `(user.id, startup.id)`
3. If found → deletes it, returns `{"saved": False, "startup_id": "..."}`
4. If not found → inserts it, returns `{"saved": True, "startup_id": "..."}`

This pattern means the frontend can call this endpoint without tracking state — the server always tells you the resulting state.

### `get_saved(user)`
Joins `Startup` through `SavedStartup`, ordered by `saved_startups.created_at` descending (most recently saved first). Returns a lightweight dict list (not full `StartupOut`) to keep the response fast.

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/saves/{startup_slug}` | Bearer | Toggle save/unsave |
| GET | `/api/v1/saves` | Bearer | List my saved startups |
