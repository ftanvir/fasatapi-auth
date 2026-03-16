from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException

from fastapi.exceptions import RequestValidationError


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers all exception handlers on the FastAPI app instance.
    Called once in main.py during app startup.
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "detail": "An unexpected error occurred",
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
            request: Request,
            exc: RequestValidationError,
    ) -> JSONResponse:
        errors = [
            {
                "field": err["loc"][-1],  # last element is the field name
                "message": err["msg"].replace("Value error, ", ""),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "message": "Validation failed",
                "data": {"errors": errors},
            },
        )