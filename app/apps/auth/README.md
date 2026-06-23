# app/apps/auth — Authentication

Handles OAuth2 social login (Google and GitHub), JWT issuance, token refresh, and logout. There is **no email/password auth** — OAuth only.

---

## How the OAuth flow works

```
Browser                     Thamani API                  Provider (Google/GitHub)
   |                             |                                  |
   |  GET /auth/google/login     |                                  |
   |  ─────────────────────────> |                                  |
   |                             | 307 Redirect to consent URL      |
   | <──────────────────────────  |                                  |
   |                             |                                  |
   | ─────────────────────────────────────────────────────────────> |
   |              User grants consent                               |
   | <───────────────────────────────────────────────────────────── |
   |                             |                                  |
   | GET /auth/google/callback?code=XXX                            |
   | ─────────────────────────> |                                   |
   |                            | Exchange code for tokens          |
   |                            | ────────────────────────────────> |
   |                            | access_token, refresh_token       |
   |                            | <────────────────────────────────  |
   |                            | Fetch user profile (email, name)  |
   |                            | <────────────────────────────────  |
   |                            | Upsert User + OAuthAccount        |
   |                            | Issue Thamani JWT pair            |
   |                            |                                   |
   | 307 Redirect to frontend with ?access_token=...&refresh_token=...|
   | <──────────────────────────|                                   |
```

The frontend receives tokens in the URL fragment and stores them locally. All subsequent requests include `Authorization: Bearer <access_token>`.

---

## Models

### `OAuthAccount`
Links a `User` to a provider identity. One user can have both Google and GitHub accounts linked. Stores the provider's access token (used for future API calls if needed).

### `RefreshToken`
Stores `token_hash` (SHA-256 of the raw refresh token). The raw token is **never persisted**. On refresh, the raw token is hashed and looked up. Token rotation: the old record is marked `revoked=True` and a new one is issued.

---

## Service (`AuthService`)

### `_get_or_create_user`
1. Looks up `OAuthAccount` by `(provider, provider_user_id)`
2. If found → updates tokens, returns existing `User`
3. If not found → looks up `User` by email (handles same email, multiple providers)
4. If no user → creates `User` and `OAuthAccount`

### `_issue_tokens`
Creates an access JWT and a refresh JWT, hashes the refresh token, persists the hash, returns the raw pair.

### `refresh`
Validates the JWT signature/expiry, checks `type=="refresh"`, looks up the hash, rotates (revoke old → issue new).

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/auth/google/login` | — | Redirect to Google consent |
| GET | `/api/v1/auth/google/callback` | — | Handle Google callback, redirect to frontend |
| GET | `/api/v1/auth/github/login` | — | Redirect to GitHub consent |
| GET | `/api/v1/auth/github/callback` | — | Handle GitHub callback, redirect to frontend |
| POST | `/api/v1/auth/refresh` | — | Rotate refresh token, get new JWT pair |
| POST | `/api/v1/auth/logout` | — | Revoke refresh token |
| GET | `/api/v1/auth/me` | Bearer | Current user summary |

---

## Providers (`providers/`)

### `google.py`
- `get_google_auth_url(state)` — builds consent URL with `openid email profile` scope
- `exchange_code_for_token(code)` — POSTs to `oauth2.googleapis.com/token`
- `get_user_info(access_token)` — GETs from `googleapis.com/oauth2/v2/userinfo`

### `github.py`
- `get_github_auth_url(state)` — builds consent URL with `read:user user:email` scope
- `exchange_code_for_token(code)` — POSTs to `github.com/login/oauth/access_token`
- `get_user_info(access_token)` — GETs `/user` and `/user/emails` (fallback for private emails)
