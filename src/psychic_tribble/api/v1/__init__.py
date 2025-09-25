"""API v1 router with comprehensive validation and error handling."""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, ValidationError
import logging

from psychic_tribble.api.routers import (
    users_router,
    events_router,
    timeslots_router,
    calendar_router,
)

logger = logging.getLogger(__name__)

# Create v1 API router
api_v1_router = APIRouter()


# Enhanced error response model
class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str
    detail: str
    request_id: str
    path: str
    timestamp: str


# Enhanced validation error response model
class ValidationErrorResponse(BaseModel):
    """Validation error response schema."""
    error: str
    detail: str
    validation_errors: list
    request_id: str
    path: str
    timestamp: str


# Request/Response models for comprehensive validation
class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    version: str
    api_version: str
    request_id: str


# Include sub-routers with enhanced configuration
api_v1_router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"],
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        422: {"model": ValidationErrorResponse, "description": "Validation Error"},
    }
)

api_v1_router.include_router(
    events_router,
    prefix="/events",
    tags=["Events"],
    responses={
        404: {"model": ErrorResponse, "description": "Event not found"},
        422: {"model": ValidationErrorResponse, "description": "Validation Error"},
    }
)

api_v1_router.include_router(
    timeslots_router,
    prefix="/timeslots",
    tags=["Timeslots"],
    responses={
        404: {"model": ErrorResponse, "description": "Timeslot not found"},
        422: {"model": ValidationErrorResponse, "description": "Validation Error"},
    }
)

api_v1_router.include_router(
    calendar_router,
    prefix="/calendar",
    tags=["Calendar"],
    responses={
        404: {"model": ErrorResponse, "description": "Calendar data not found"},
        422: {"model": ValidationErrorResponse, "description": "Validation Error"},
    }
)


# API v1 root endpoint
@api_v1_router.get(
    "/",
    response_model=HealthResponse,
    tags=["API Info"],
    summary="API v1 information"
)
async def api_v1_info(request: Request):
    """Get API v1 information and status."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    return HealthResponse(
        status="operational",
        version="1.0.0",
        api_version="v1",
        request_id=request_id
    )


# API versioning information
@api_v1_router.get(
    "/info",
    tags=["API Info"],
    summary="Detailed API information"
)
async def api_info(request: Request):
    """Get detailed API information including available endpoints."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    return {
        "api_version": "v1",
        "service": "psychic-tribble-api",
        "version": "1.0.0",
        "request_id": request_id,
        "endpoints": {
            "users": "/v1/users",
            "events": "/v1/events",
            "timeslots": "/v1/timeslots",
            "calendar": "/v1/calendar"
        },
        "documentation": {
            "openapi": "/openapi.json",
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        },
        "monitoring": {
            "health": "/health",
            "metrics": "/metrics",
            "ready": "/ready",
            "live": "/live"
        }
    }