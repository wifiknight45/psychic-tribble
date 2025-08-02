import os
import logging

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import your routers
from pyschic_tribble.routes.users     import users_router
from pyschic_tribble.routes.events    import events_router
from pyschic_tribble.routes.timeslots import timeslots_router
from pyschic_tribble.routes.calendar  import calendar_router

# -----------------------------------------------------------------------------
# 1. Configuration & Logging
# -----------------------------------------------------------------------------
ENV         = os.getenv("PYTT_ENV", "development")
DB_URL      = os.getenv("DATABASE_URL", f"sqlite:///./{ENV}.db")
APP_TITLE   = "Psychic Tribble"
APP_VERSION = "1.0.0"

logging.basicConfig(
    level=logging.DEBUG if ENV == "development" else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("uvicorn.error")

# -----------------------------------------------------------------------------
# 2. Database Setup (SQLAlchemy)
# -----------------------------------------------------------------------------
engine       = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------------------------------------
# 3. FastAPI Instantiation
# -----------------------------------------------------------------------------
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    debug=(ENV == "development")
)

# -----------------------------------------------------------------------------
# 4. Middleware
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# 5. Health Check & Root
# -----------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def root():
    return {"message": f"Welcome to {APP_TITLE} v{APP_VERSION}"}

# -----------------------------------------------------------------------------
# 6. Exception Handlers
# -----------------------------------------------------------------------------
@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse({"detail": "Resource not found"}, status_code=404)


@app.exception_handler(500)
async def server_error(request: Request, exc):
    logger.error(f"Server error: {exc}")
    return JSONResponse({"detail": "Internal server error"}, status_code=500)

# -----------------------------------------------------------------------------
# 7. Include Routers (with Dependencies)
# -----------------------------------------------------------------------------
app.include_router(
    users_router,
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_db)]
)

app.include_router(
    events_router,
    prefix="/events",
    tags=["Events"],
    dependencies=[Depends(get_db)]
)

app.include_router(
    timeslots_router,
    prefix="/timeslots",
    tags=["Timeslots"],
    dependencies=[Depends(get_db)]
)

app.include_router(
    calendar_router,
    prefix="/calendar",
    tags=["Calendar"],
    dependencies=[Depends(get_db)]
)

# -----------------------------------------------------------------------------
# 8. Uvicorn Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=(ENV == "development"),
        log_level="debug" if ENV == "development" else "info"
    )

