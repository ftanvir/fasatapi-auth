from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.handlers import register_exception_handlers
from app.db.redis import redis_client
from app.api.v1.router import v1_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await redis_client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    register_exception_handlers(app)
    app.include_router(v1_router)

    return app


app = create_app()