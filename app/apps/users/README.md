# app/apps/users — User Profiles

Manages founder profiles — both the private view (for the authenticated user) and the public view (for anyone browsing the platform).

---

## Model — `User`

| Field | Notes |
|-------|-------|
| `id` | UUID string primary key |
| `email` | Unique, indexed |
| `full_name` | Set from OAuth provider on first login |
| `avatar_url` | Set from OAuth provider, user can update |
| `bio`, `twitter_handle`, `website_url` | Optional, user-editable |
| `country` | Defaults to `"Tanzania"` |
| `primary_provider` | `"google"` or `"github"` |
| `is_verified` | Set to `True` on first successful OAuth login |
| `is_active` | Soft-delete flag |
| `is_admin` | Manual flag, not exposed via any public endpoint |

---

## Schemas

### `UserPublicOut`
Returned for any user's public profile (`GET /users/{user_id}`). Includes `startup_count` (computed — count of active startups by this founder). Does **not** include email or provider info.

### `UserPrivateOut`
Extends `UserPublicOut` with `email`, `is_verified`, and `primary_provider`. Returned only to the authenticated user (`GET /users/me`).

### `UserUpdateIn`
Partial update — all fields optional. Only `full_name`, `bio`, `twitter_handle`, `website_url`, and `country` are user-editable.

---

## Service — `UserService`

- `get_by_id(user_id)` — simple lookup by primary key
- `_startup_count(user_id)` — COUNT query on active startups for this founder
- `get_public_profile(user)` — builds `UserPublicOut` including startup count
- `get_private_profile(user)` — builds `UserPrivateOut` including startup count
- `update_profile(user, data)` — applies partial update, sets `updated_at`, returns new private profile

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/users/me` | Bearer | My full private profile |
| PATCH | `/api/v1/users/me` | Bearer | Update my profile |
| GET | `/api/v1/users/{user_id}` | — | Any user's public profile |
