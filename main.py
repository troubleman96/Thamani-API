from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.core.exceptions import http_exception_handler, validation_exception_handler
from app.core.middleware import RequestLoggingMiddleware
from app.core.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
    await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Verified startup revenue marketplace for East Africa",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    API_PREFIX = "/api/v1"

    # Routers are registered as each app phase is built
    from app.apps.auth.router import router as auth_router
    from app.apps.users.router import router as users_router
    from app.apps.startups.router import router as startups_router
    from app.apps.revenue.router import router as revenue_router
    from app.apps.verification.router import router as verification_router
    from app.apps.listings.router import router as listings_router
    from app.apps.offers.router import router as offers_router
    from app.apps.leaderboard.router import router as leaderboard_router
    from app.apps.saves.router import router as saves_router
    from app.apps.stats.router import router as stats_router

    app.include_router(auth_router,         prefix=API_PREFIX)
    app.include_router(users_router,        prefix=API_PREFIX)
    app.include_router(startups_router,     prefix=API_PREFIX)
    app.include_router(revenue_router,      prefix=API_PREFIX)
    app.include_router(verification_router, prefix=API_PREFIX)
    app.include_router(listings_router,     prefix=API_PREFIX)
    app.include_router(offers_router,       prefix=API_PREFIX)
    app.include_router(leaderboard_router,  prefix=API_PREFIX)
    app.include_router(saves_router,        prefix=API_PREFIX)
    app.include_router(stats_router,        prefix=API_PREFIX)

    @app.get("/", tags=["Health"])
    async def health():
        return {
            "success": True,
            "message": f"{settings.APP_NAME} is running",
            "version": settings.APP_VERSION,
        }

    @app.get("/ping", tags=["Health"])
    async def ping():
        return {"ping": "pong"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
