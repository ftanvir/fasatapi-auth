from collections.abc import AsyncGenerator

from arq.connections import ArqRedis, RedisSettings, create_pool

from app.core.config import get_settings

settings = get_settings()

redis_pool: ArqRedis | None = None


async def get_redis_pool() -> ArqRedis:
    global redis_pool
    if redis_pool is None:
        redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
        redis_pool = await create_pool(redis_settings)
    return redis_pool


async def close_redis_pool() -> None:
    global redis_pool
    if redis_pool is not None:
        await redis_pool.close()
        redis_pool = None


async def get_redis() -> AsyncGenerator[ArqRedis, None]:
    pool = await get_redis_pool()
    yield pool

def decode_redis_value(value: bytes | str | None) -> str | None:
    """Decodes Redis bytes response to string."""
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value