import os
import logging
import traceback

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session

from alembic.config import Config as AlembicConfig
from alembic import command

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import _rate_limit_exceeded_handler

from config import settings
from psychic_tribble.db.base import Base
from psychic_tribble.routes.users import users_router
from psychic_tribble.routes.events import events_router
from psychic_tribble.routes.timeslots import timeslots_router
from psychic_tribble.routes.calendar import calendar_router

# -----------------------------------------------------------------------------
# Configuration & Logging
# -----------------------------------------------------------------------------
ENV = os.getenv("PYTT_ENV", "development")
DEBUG = ENV == "development"

APP_TITLE   = "Psychic Tribble"
APP_VERSION = "1.0.0"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///./{ENV}.db")
ALEMBIC_INI  = os.getenv("ALEMBIC_INI", "alembic.ini")

# CORS origins & rate limits come from config or env
CORS_ORIGINS = getattr(settings, "CORS_ORIGINS", [])
RATE_LIMITS  = getattr(settings, "RATE_LIMITS", ["100/minute"])
MAX_BODY_SIZE = int(os.getenv("MAX_BODY_SIZE", 10 * 1024 * 1024))  # 10 MB

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("uvicorn.error")

# -----------------------------------------------------------------------------
# Database Setup
# -----------------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    echo=DEBUG,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Yield a database session and ensure proper teardown."""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error("Database session error: %s", str(e))
        raise HTTPException(500, "Database error")
    finally:
        db.close()

# -----------------------------------------------------------------------------
# Application Factory
# -----------------------------------------------------------------------------
def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        debug=DEBUG,
        # built-in max request size (Starlette 0.27+)
        max_request_size=MAX_BODY_SIZE
    )

    # -----------------------------------------------------------------------------
    # Run Alembic migrations on startup
    # -----------------------------------------------------------------------------
    @app.on_event("startup")
    def run_migrations():
        logger.info("Running Alembic migrations (head)")
        alembic_cfg = AlembicConfig(ALEMBIC_INI)
        command.upgrade(alembic_cfg, "head")

    # -----------------------------------------------------------------------------
    # CORS Middleware (hardened for prod)
    # -----------------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS or ["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )

    # -----------------------------------------------------------------------------
    # Rate Limiting Middleware
    # -----------------------------------------------------------------------------
    limiter = Limiter(key_func=get_remote_address, default_limits=RATE_LIMITS)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # -----------------------------------------------------------------------------
    # Exception Handlers
    # -----------------------------------------------------------------------------
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Validation error on %s: %s", request.url, exc.errors())
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()}
        )

    @app.exception_handler(404)
    async def not_found(request: Request, exc):
        return JSONResponse({"detail": "Resource not found"}, status_code=404)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def server_error(request: Request, exc: Exception):
        error_id = os.urandom(8).hex()
        tb = traceback.format_exc()
        logger.error("Error ID %s on %s: %s\n%s", error_id, request.url, str(exc), tb)
        return JSONResponse(
            {"detail": "Internal server error", "error_id": error_id},
            status_code=500
        )

    # -----------------------------------------------------------------------------
    # Health-check & Root
    # -----------------------------------------------------------------------------
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok"}

    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": f"Welcome to {APP_TITLE} v{APP_VERSION}"}

    # -----------------------------------------------------------------------------
    # Include Routers
    # -----------------------------------------------------------------------------
    for router, prefix, tag in [
        (users_router,     "/users",     "Users"),
        (events_router,    "/events",    "Events"),
        (timeslots_router, "/timeslots", "Timeslots"),
        (calendar_router,  "/calendar",  "Calendar"),
    ]:
        app.include_router(
            router,
            prefix=prefix,
            tags=[tag],
            dependencies=[Depends(get_db)]
        )

    return app

# Instantiate ASGI app
app = create_app()

# -----------------------------------------------------------------------------
# Uvicorn Entrypoint (local dev)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info"
    )
