from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import v1_router
from app.core.config import get_settings
from app.core.handlers import register_exception_handlers
from app.db.redis import close_redis_pool, get_redis_pool

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup — initialize Redis pool
    await get_redis_pool()
    yield
    # shutdown — close Redis pool cleanly
    await close_redis_pool()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    register_exception_handlers(app)
    app.include_router(v1_router)

    return app


app = create_app()