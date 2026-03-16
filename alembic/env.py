import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.db.base import Base

from app.modules.auth.model import User, RefreshToken

# ─── Alembic Config ───────────────────────────────────────────────────────────

config = context.config
settings = get_settings()

# sets up Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# tells Alembic which models to track for autogenerate
target_metadata = Base.metadata


# ─── Run Migrations ───────────────────────────────────────────────────────────

def run_migrations_offline() -> None:
    """
    Run migrations without a DB connection.
    Useful for generating SQL scripts to review before applying.
    """
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,        # detects column type changes
        compare_server_default=True,  # detects default value changes
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations with a live async DB connection.
    """
    engine = create_async_engine(settings.DATABASE_URL)

    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


# ─── Entry Point ──────────────────────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())