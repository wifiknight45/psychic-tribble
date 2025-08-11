import os
import logging
from pathlib import Path
from datetime import datetime, timedelta

import pytz
from icalendar import Calendar as iCalCalendar, Event as iCalEvent

from fastapi import (
    FastAPI, Depends, HTTPException, Request, Response, status, Query
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from pydantic import BaseModel, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
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

    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///./{env}.db")
    alembic_ini: str = os.getenv("ALEMBIC_INI", "alembic.ini")

    secret_key: str = os.getenv("SECRET_KEY", "PLEASE_CHANGE_ME")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 14  # 14 days

    # If not provided, we’ll use sensible dev defaults in create_app()
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

def _encode_token(data: dict, minutes: int) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

def create_access_token(sub: str) -> str:
    return _encode_token({"sub": sub, "type": "access"}, settings.access_token_expire_minutes)

def create_refresh_token(sub: str) -> str:
    return _encode_token({"sub": sub, "type": "refresh"}, settings.refresh_token_expire_minutes)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def decode_access_token(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid access token type")
    return payload

def decode_refresh_token(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token type")
    return payload

# -----------------------------------------------------------------------------
# Database Setup (Sync)
# -----------------------------------------------------------------------------
engine = create_engine(
    str(settings.database_url),
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"check_same_thread": False} if str(settings.database_url).startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
# Pydantic Schemas
# -----------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def ensure_aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=pytz.UTC)
    return dt.astimezone(pytz.UTC)

# -----------------------------------------------------------------------------
# Application Factory
# -----------------------------------------------------------------------------
def create_app() -> FastAPI:
    if settings.secret_key == "PLEASE_CHANGE_ME" and not settings.debug:
        raise RuntimeError("SECRET_KEY must be set securely in production!")

    app = FastAPI(
        title="Psychic Tribble",
        version="1.0.0",
        debug=settings.debug,
    )

    # Mount static files (tolerate missing directory in dev/CI)
    static_dir = Path("static")
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    else:
        logger.warning("Static directory not found; skipping mount.")

    # Auto-migrate in development only
    @app.on_event("startup")
    def run_migrations():
        if settings.debug:
            logger.info("Running Alembic migrations")
            alembic_cfg = AlembicConfig(str(ALEMBIC_PATH))
            command.upgrade(alembic_cfg, "head")

    # Global exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"errors": exc.errors(), "body": exc.body})

    register_exception_handlers(app)

    # CORS
    default_dev_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",  # if serving frontend statically from same port
    ]
    origins = settings.cors_origins or (default_dev_origins if settings.debug else ["https://yourdomain.com"])
    allow_credentials = "*" not in origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting backed by Redis (fallback in-memory if Redis unavailable)
    try:
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=settings.rate_limits or ["100/minute"],
            storage=RedisStorage(settings.redis_url),
        )
        logger.info("Rate limiter initialized with Redis storage")
    except Exception as e:
        logger.warning("Redis storage unavailable for rate limiting, falling back to in-memory: %s", e)
        limiter = Limiter(key_func=get_remote_address, default_limits=settings.rate_limits or ["100/minute"])
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # -----------------------------------------------------------------------------
    # Authentication Endpoints
    # -----------------------------------------------------------------------------
    @app.post("/register", tags=["Auth"], status_code=201)
    async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        user = User(email=payload.email, hashed_password=hash_password(payload.password))
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Email already registered")
        return {"message": "User registered successfully"}

    @app.post("/token", tags=["Auth"])
    async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db),
    ):
        user = db.query(User).filter(User.email == form_data.username).first()
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(user.email)
        refresh_token = create_refresh_token(user.email)
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    @app.post("/refresh", tags=["Auth"])
    async def refresh_access_token(payload: RefreshRequest):
        data = decode_refresh_token(payload.refresh_token)
        email = data.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        # Rotate tokens for better security
        new_access = create_access_token(email)
        new_refresh = create_refresh_token(email)
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}

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
    # Core Routers (protect events/timeslots/calendar; keep users_router flexible)
    # -----------------------------------------------------------------------------
    app.include_router(users_router, prefix="/users", tags=["Users"])
    for router, prefix, tag in [
        (events_router,    "/events",    "Events"),
        (timeslots_router, "/timeslots", "Timeslots"),
        (calendar_router,  "/calendar",  "Calendar"),
    ]:
        app.include_router(
            router,
            prefix=prefix,
            tags=[tag],
            dependencies=[Depends(get_db), Depends(get_current_user)],
        )

    # -----------------------------------------------------------------------------
    # Health check
    # -----------------------------------------------------------------------------
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok"}

    # -----------------------------------------------------------------------------
    # RFC 5545–compliant iCalendar feed
    # Supports either Authorization header (Bearer) or a `?token=` query param.
    # -----------------------------------------------------------------------------
    @app.get(
        "/calendar/feed.ics",
        response_class=Response,
        tags=["Calendar"],
        summary="Get your calendar as an RFC 5545 iCalendar feed"
    )
    async def ics_feed(
        request: Request,
        token: str | None = Query(default=None),
        db: Session = Depends(get_db),
    ):
        current_user: User | None = None

        if token:
            # Allow query token for calendar clients that can't set headers
            payload = decode_access_token(token)
            email = payload.get("sub")
            if not email:
                raise HTTPException(status_code=401, detail="Invalid token")
            current_user = db.query(User).filter(User.email == email).first()
            if not current_user:
                raise HTTPException(status_code=401, detail="User not found")
        else:
            # Fallback to normal Authorization header
            bearer_token = await oauth2_scheme(request)
            payload = decode_access_token(bearer_token)
            email = payload.get("sub")
            current_user = db.query(User).filter(User.email == email).first()
            if not current_user:
                raise HTTPException(status_code=401, detail="User not found")

        # Build the calendar
        cal = iCalCalendar()
        cal.add("prodid", "-//Psychic Tribble//EN")
        cal.add("version", "2.0")

        # Fetch all events for this user
        events = db.query(Event).filter(Event.user_id == current_user.id).all()

        for ev in events:
            component = iCalEvent()
            component.add("uid", f"{ev.id}@psychic-tribble")
            component.add("dtstamp", ensure_aware_utc(datetime.utcnow()))
            component.add("dtstart", ensure_aware_utc(ev.start_time))
            component.add("dtend", ensure_aware_utc(ev.end_time))
            if ev.title:
                component.add("summary", ev.title)
            if getattr(ev, "description", None):
                component.add("description", ev.description)
            if getattr(ev, "location", None):
                component.add("location", ev.location)
            cal.add_component(component)

        ical_bytes = cal.to_ical()
        headers = {"Content-Disposition": 'attachment; filename="calendar.ics"'}
        return Response(content=ical_bytes, media_type="text/calendar; charset=utf-8", headers=headers)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    reload_flag = settings.debug
    workers = 1 if reload_flag else int(os.getenv("WORKERS", "4"))
    uvicorn.run(
        "app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=reload_flag,
        workers=workers,
        log_level="debug" if settings.debug else "info",
    )

