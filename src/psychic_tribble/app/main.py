"""
Psychic Tribble API - Main application entry point.
Refactored for Parrot 6.2 Smoke Testing.
"""
import logging
import uuid
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

# Import modular components
try:
    from psychic_tribble.config import get_settings
    from psychic_tribble.api.v1 import api_v1_router
    from psychic_tribble.middleware.request_id import RequestIDMiddleware
    from psychic_tribble.middleware.security_headers import SecurityHeadersMiddleware
    from psychic_tribble.dependencies.exception_handlers import register_exception_handlers
    from psychic_tribble.core.logging_setup import configure_logging
    from psychic_tribble.core.monitoring import init_metrics
    from psychic_tribble.core.database import init_database_pool
except ImportError as e:
    print(f"CRITICAL: Missing module inside 'src'. Ensure you use --app-dir src. Error: {e}")
    sys.exit(1)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with error handling for smoke tests."""
    configure_logging(settings)
    logger = logging.getLogger(__name__)
    logger.info("Starting Psychic Tribble API...")
    
    # 1. Initialize database connection pool (Graceful failure for smoke tests)
    try:
        await init_database_pool(settings)
        logger.info("Database connection pool initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}. (Verify aiosqlite is installed for SQLite)")
        if settings.ENV == "production":
            raise e

    # 2. Initialize metrics
    try:
        init_metrics(app)
    except Exception as e:
        logger.warning(f"Metrics initialization skipped/failed: {e}")
    
    logger.info(f"Application startup complete in {settings.ENV} mode")
    
    yield
    
    logger.info("Shutting down Psychic Tribble API...")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Configure API documentation
    docs_config = {
        "docs_url": "/docs" if settings.ENV != "production" else None,
        "redoc_url": "/redoc" if settings.ENV != "production" else None,
        "openapi_url": "/openapi.json" if settings.ENV != "production" else None,
    }
    
    app = FastAPI(
        title="Psychic Tribble API",
        version="1.0.0",
        lifespan=lifespan,
        **docs_config
    )
    
    # ---------------------
    # Middleware Configuration
    # ---------------------
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS, # Matches your .env key
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"]
    )
    
    if settings.ENABLE_HTTPS_REDIRECT:
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # 5. Rate limiting - Force in-memory if Redis is unavailable
    storage_uri = settings.REDIS_URL if settings.ENV == "production" else "memory://"
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[settings.DEFAULT_RATE_LIMIT],
        storage_uri=storage_uri
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    register_exception_handlers(app)

    # ---------------------
    # API Routes
    # ---------------------
    app.include_router(api_v1_router, prefix="/v1")

    @app.get("/", tags=["Health"])
    async def root(request: Request):
        return {
            "message": "Psychic Tribble API - Backend operational",
            "environment": settings.ENV,
            "request_id": getattr(request.state, "request_id", "unknown")
        }

    @app.get("/health", tags=["Health"])
    async def health_check(request: Request):
        return {
            "status": "healthy",
            "database": "sqlite", 
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    
    return app

app = create_app()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logging.error(f"Unhandled exception [ID: {request_id}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "request_id": request_id}
    )
