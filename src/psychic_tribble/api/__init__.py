"""API router configuration."""
from fastapi import APIRouter

from .routers import (
    users_router,
    events_router,
    timeslots_router,
    calendar_router,
)

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(events_router, prefix="/events", tags=["Events"])
api_router.include_router(timeslots_router, prefix="/timeslots", tags=["Timeslots"])
api_router.include_router(calendar_router, prefix="/calendar", tags=["Calendar"])