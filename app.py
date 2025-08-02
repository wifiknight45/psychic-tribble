import os
import logging
import traceback

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session

from config import settings
from psychic_tribble.db.base import Base  # SQLAlchemy declarative base
from psychic_tribble.routes.users import users_router
from psychic_tribble.routes.events import events_router
from psychic_tribble.routes.timeslots import timeslots_router
from psychic_tribble.routes.calendar import calendar_router

# -----------------------------------------------------------------------------
# Configuration & Logging
# -----------------------------------------------------------------------------
ENV = os.getenv("PYTT_ENV", "development")
DEBUG = ENV == "development"
APP_TITLE = "Psychic Tribble"
APP_VERSION = "1.0.0"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///./{ENV}.db")

# CORS
CORS_ORIGINS = settings.CORS_ORIGINS if hasattr(settings, "CORS_ORIGINS") else ["*"]
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
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Yield a database session and ensure it's closed."""
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
        max_request_size=MAX_BODY_SIZE
    )

    # Create tables on startup
    @app.on_event("startup")
    def on_startup():
        logger.info("Creating database tables (if not exist)")
        Base.metadata.create_all(bind=engine)

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=3600
    )

    # Exception Handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Validation error: %s", exc.errors())
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
        logger.error("Error ID %s: %s\n%s", error_id, str(exc), tb)
        return JSONResponse(
            {"detail": "Internal server error", "error_id": error_id},
            status_code=500
        )

    # Health-check
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok"}

    # Root endpoint (hidden)
    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": f"Welcome to {APP_TITLE} v{APP_VERSION}"}

    # Include Routers
    for router, prefix, tag in [
        (users_router, "/users", "Users"),
        (events_router, "/events", "Events"),
        (timeslots_router, "/timeslots", "Timeslots"),
        (calendar_router, "/calendar", "Calendar")
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
# Uvicorn Entrypoint (local development)
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
