import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from alembic import context

# Import all models so Alembic can detect them
from app.apps.users.models import User  # noqa: F401
from app.apps.auth.models import OAuthAccount, RefreshToken  # noqa: F401
from app.apps.startups.models import Startup  # noqa: F401
from app.apps.revenue.models import RevenueSnapshot  # noqa: F401
from app.apps.verification.models import VerificationCredential  # noqa: F401
from app.apps.listings.models import Listing  # noqa: F401
from app.apps.offers.models import Offer  # noqa: F401
from app.apps.saves.models import SavedStartup  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
