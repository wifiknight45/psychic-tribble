# psychic_tribble/utils.py

import os
import traceback
import logging

from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger("uvicorn.error")

def handle_request_validation_error(request: Request, exc: RequestValidationError):
    logger.warning("Validation error on %s: %s", request.url, exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

def handle_not_found_error(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": "Resource not found"})

def handle_http_exception(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

def handle_server_error(request: Request, exc: Exception):
    error_id = os.urandom(8).hex()
    tb = traceback.format_exc()
    logger.error("Error ID %s on %s: %s\n%s", error_id, request.url, str(exc), tb)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_id": error_id},
    )

def register_exception_handlers(app):
    """
    Attach global exception handlers to the FastAPI app.
    """
    app.add_exception_handler(RequestValidationError, handle_request_validation_error)
    app.add_exception_handler(404, handle_not_found_error)
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(Exception, handle_server_error)
