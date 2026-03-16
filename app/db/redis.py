from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import get_settings

settings = get_settings()

# ─── Redis Client ─────────────────────────────────────────────────────────────

# single client instance, connection pool managed internally
redis_client = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,    # returns str instead of bytes
)


# ─── Dependency ───────────────────────────────────────────────────────────────

async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    FastAPI dependency that yields the Redis client.
    Uses a single shared client with internal connection pooling.
    """
    yield redis_client