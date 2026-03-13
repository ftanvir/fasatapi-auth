from fastapi import FastAPI

from app.core.config import get_settings
from app.core.handlers import register_exception_handlers

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    register_exception_handlers(app)

    # routers will be registered here later
    # from app.api.v1.router import v1_router
    # app.include_router(v1_router)

    return app


app = create_app()