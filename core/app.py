import os
import logging
from pathlib import Path
from datetime import datetime, timedelta

import pytz
from icalendar import Calendar as iCalCalendar, Event as iCalEvent

from fastapi import (
    FastAPI, Depends, HTTPException, Request, Response, status
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session
from alembic.config import Config as AlembicConfig
from alembic import command

from passlib.context import CryptContext
from jose import JWTError, jwt

from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.storage.redis import RedisStorage

from psychic_tribble.db.base import Base
from psychic_tribble.db.models import User, Event
from psychic_tribble.routes import (
    users_router, events_router, timeslots_router, calendar_router
)
from psychic_tribble.utils import register_exception_handlers

# -----------------------------------------------------------------------------
# Settings via environment / .env
# -----------------------------------------------------------------------------
class Settings(BaseSettings):
    env: str = os.getenv("PYTT_ENV", "development")
    debug: bool = env == "development"
    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///./{env}.db"
    )
    alembic_ini: str = os.getenv("ALEMBIC_INI", "alembic.ini")
    secret_key: str = os.getenv("SECRET_KEY", "PLEASE_CHANGE_ME")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: list[str] = []
    rate_limits: list[str] = []
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()
ALEMBIC_PATH = Path(__file__).parent / settings.alembic_ini

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("uvicorn.error")

# -----------------------------------------------------------------------------
# Cryptography & Auth Utilities
# -----------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# -----------------------------------------------------------------------------
# Database Setup (Sync)
# -----------------------------------------------------------------------------
engine = create_engine(
    str(settings.database_url),
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"check_same_thread": False}
    if str(settings.database_url).startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)
Base.metadata.bind = engine

def get_db() -> Session:
    session = SessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error("DB session error: %s", e)
        raise HTTPException(500, "Database error")
    finally:
        session.close()

# -----------------------------------------------------------------------------
# Application Factory
# -----------------------------------------------------------------------------
def create_app() -> FastAPI:
    app = FastAPI(
        title="Psychic Tribble",
        version="1.0.0",
        debug=settings.debug,
    )

    # Mount static files for future HTML/CSS/JS
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Auto-migrate in development only
    @app.on_event("startup")
    def run_migrations():
        if settings.debug:
            logger.info("Running Alembic migrations")
            alembic_cfg = AlembicConfig(str(ALEMBIC_PATH))
            command.upgrade(alembic_cfg, "head")

    # Global exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={"errors": exc.errors(), "body": exc.body},
        )

    register_exception_handlers(app)

    # CORS
    origins = (
        settings.cors_origins
        or (["*"] if settings.debug else ["https://yourdomain.com"])
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting backed by Redis
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=settings.rate_limits or ["100/minute"],
        storage=RedisStorage(settings.redis_url),
    )
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # -----------------------------------------------------------------------------
    # Authentication Endpoints
    # -----------------------------------------------------------------------------
    @app.post("/token", tags=["Auth"])
    async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db),
    ):
        user = (
            db.query(User)
            .filter(User.email == form_data.username)
            .first()
        )
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token({"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}

    async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
    ):
        payload = decode_access_token(token)
        email = payload.get("sub")
        if email is None:
            raise HTTPException(401, "Invalid token")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(401, "User not found")
        return user

    # -----------------------------------------------------------------------------
    # Core Routers (all require auth & DB)
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
            dependencies=[
                Depends(get_db),
                Depends(get_current_user),
            ],
        )

    # -----------------------------------------------------------------------------
    # Health check
    # -----------------------------------------------------------------------------
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok"}

    # -----------------------------------------------------------------------------
    # New: RFC 5545–compliant iCalendar feed
    # -----------------------------------------------------------------------------
    @app.get(
        "/calendar/feed.ics",
        response_class=Response,
        tags=["Calendar"],
        summary="Get your calendar as an RFC 5545 iCalendar feed"
    )
    async def ics_feed(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        # Build the calendar
        cal = iCalCalendar()
        cal.add("prodid", "-//Psychic Tribble//EN")
        cal.add("version", "2.0")

        # Fetch all events for this user
        events = db.query(Event).filter(Event.user_id == current_user.id).all()

        utc = pytz.UTC
        for ev in events:
            component = iCalEvent()
            component.add("uid", f"{ev.id}@psychic-tribble")
            component.add("dtstamp", datetime.utcnow().replace(tzinfo=utc))
            component.add("dtstart", ev.start_time.astimezone(utc))
            component.add("dtend", ev.end_time.astimezone(utc))
            component.add("summary", ev.title)
            if ev.description:
                component.add("description", ev.description)
            if getattr(ev, "location", None):
                component.add("location", ev.location)
            cal.add_component(component)

        ical_bytes = cal.to_ical()
        return Response(content=ical_bytes, media_type="text/calendar; charset=utf-8")

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=settings.debug,
        workers=4,
        log_level="debug" if settings.debug else "info",
    )

