"""Exception handlers for the application."""
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: HTTPException):
    """Handle validation errors."""
    logger.warning(f"Validation error on {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.detail,
            "path": str(request.url.path)
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please contact support.",
            "path": str(request.url.path)
        }
    )


def register_exception_handlers(app: FastAPI):
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(HTTPException, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)