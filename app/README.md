# app — Application Package

The `app/` package contains all application code. It is split into two sub-packages:

```
app/
├── core/     Cross-cutting infrastructure shared by all apps
└── apps/     Self-contained domain modules
```

- **[`core/`](core/README.md)** — config, database, Redis, JWT security, response envelope, exception handlers, pagination helpers, request logging middleware, and FastAPI dependency functions. Nothing in `core/` knows about any specific domain.

- **[`apps/`](apps/README.md)** — one subdirectory per domain (auth, users, startups, revenue, verification, listings, offers, saves, leaderboard, stats). Each app is independently understandable — it owns its models, schemas, service, and router.

---

## Dependency direction

```
apps/*/router.py
      │
      ▼
apps/*/service.py  ←──── imports models from sibling apps (for relationships)
      │
      ▼
apps/*/models.py
      │
      ▼
core/              ←──── never imports from apps/
```

`core/` has zero knowledge of any app. Apps freely import from `core/`. Apps import **models** from sibling apps (e.g. `startups/service.py` imports `Listing` to join on it) but never import sibling services or routers.
