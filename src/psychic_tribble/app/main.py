"""
Psychic Tribble API - Main application entry point.

This is the refactored main.py with improved:
- API versioning (/v1/ prefix)
- Request ID middleware for correlation tracking
- Comprehensive input validation with Pydantic
- Database connection pooling configuration
- Secrets management preparation
- Environment-based API documentation
- Enhanced security headers and middleware
- Modular code organization
"""
import logging
import uuid
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
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

# Import our modular components
from psychic_tribble.config import get_settings
from psychic_tribble.api.v1 import api_v1_router
from psychic_tribble.middleware.request_id import RequestIDMiddleware
from psychic_tribble.middleware.security_headers import SecurityHeadersMiddleware
from psychic_tribble.dependencies.exception_handlers import register_exception_handlers
from psychic_tribble.core.logging_setup import configure_logging
from psychic_tribble.core.monitoring import init_metrics
from psychic_tribble.core.database import init_database_pool

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    configure_logging(settings)
    logger = logging.getLogger(__name__)
    logger.info("Starting Psychic Tribble API...")
    
    # Initialize database connection pool
    await init_database_pool(settings)
    
    # Initialize metrics
    init_metrics(app)
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Psychic Tribble API...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Configure API documentation based on environment
    docs_config = {}
    if settings.ENV == "production":
        # Disable API docs in production
        docs_config = {
            "docs_url": None,
            "redoc_url": None,
            "openapi_url": None
        }
    else:
        # Enable API docs for development/testing
        docs_config = {
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "openapi_url": "/openapi.json"
        }
    
    app = FastAPI(
        title="Psychic Tribble API",
        description="Secure, scalable, and maintainable backend for the Psychic Tribble platform.",
        version="1.0.0",
        contact={
            "name": "Psychic Tribble Dev Team",
            "email": "support@psychictribble.com",
            "url": "https://psychictribble.com/contact"
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        },
        lifespan=lifespan,
        **docs_config
    )
    
    # ---------------------
    # Middleware Configuration (Order matters!)
    # ---------------------
    
    # 1. Request ID middleware (first to capture all requests)
    app.add_middleware(RequestIDMiddleware)
    
    # 2. Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 3. CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"]  # Expose request ID to clients
    )
    
    # 4. HTTPS redirect (if enabled)
    if settings.enable_https_redirect:
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # 5. Rate limiting middleware (last middleware layer)
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[settings.default_rate_limit]
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    # ---------------------
    # Exception Handlers
    # ---------------------
    register_exception_handlers(app)
    
    # ---------------------
    # API Routes with Versioning
    # ---------------------
    
    # Include v1 API router with /v1 prefix
    app.include_router(
        api_v1_router,
        prefix="/v1",
        responses={
            404: {"description": "Not found"},
            422: {"description": "Validation Error"},
            429: {"description": "Rate limit exceeded"},
            500: {"description": "Internal server error"}
        }
    )
    
    # ---------------------
    # Root Health Check
    # ---------------------
    @app.get("/", tags=["Health"], summary="Root health check")
    async def root(request: Request):
        """Root endpoint for basic health check."""
        request_id = getattr(request.state, "request_id", "unknown")
        return {
            "message": "Psychic Tribble API - Backend operational",
            "version": "1.0.0",
            "api_version": "v1",
            "request_id": request_id,
            "status": "healthy"
        }
    
    # ---------------------
    # Additional Health Endpoints
    # ---------------------
    @app.get("/health", tags=["Health"], summary="Detailed health check")
    async def health_check(request: Request):
        """Detailed health check endpoint."""
        request_id = getattr(request.state, "request_id", "unknown")
        
        # In a real implementation, you'd check database connectivity, 
        # external services, etc.
        health_status = {
            "status": "healthy",
            "service": "psychic-tribble-api",
            "version": "1.0.0",
            "environment": settings.ENV,
            "request_id": request_id,
            "checks": {
                "database": "healthy",  # Would be actual DB check
                "redis": "healthy",     # Would be actual Redis check
            }
        }
        
        return health_status
    
    return app


# Create the application instance
app = create_app()


# Global exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with request ID correlation."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logging.error(
        f"Unhandled exception [Request ID: {request_id}]: {exc}",
        exc_info=True,
        extra={"request_id": request_id}
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please contact support.",
            "request_id": request_id,
            "path": str(request.url.path)
        }
    )
