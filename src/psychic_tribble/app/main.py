import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from psychic_tribble.config import get_settings
from psychic_tribble.dependencies.exception_handlers import register_exception_handlers
from psychic_tribble.api import api_router

from psychic_tribble.security.security_headers import SecurityHeadersMiddleware
from psychic_tribble.logging_setup import configure_logging
from psychic_tribble.monitoring import init_metrics

settings = get_settings()

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
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ---------------------
# Configure Logging & Monitoring
configure_logging(settings)
init_metrics(app)

# ---------------------
# Security: CORS, HTTPS, Security Headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
if settings.enable_https_redirect:
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(SecurityHeadersMiddleware)

# ---------------------
# Rate Limiting Setup (using SlowAPI)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.default_rate_limit}"]
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ---------------------
# Register Custom Exception Handlers
register_exception_handlers(app)

# ---------------------
# Include Modular Routers (API endpoints)
app.include_router(api_router)

# ---------------------
# Root route for basic health check
@app.get("/", tags=["Internal"])
async def root():
    return {"message": "Psychic Tribble API - Backend operational"}

# ---------------------
# Global Error Handler Example
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please contact support."}
    )
