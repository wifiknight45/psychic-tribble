"""Monitoring and metrics setup."""
import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def init_metrics(app: FastAPI) -> None:
    """Initialize application metrics and monitoring."""
    
    # Add basic health check endpoint for monitoring
    @app.get("/health", tags=["Monitoring"])
    async def health_check():
        """Health check endpoint for monitoring systems."""
        return {
            "status": "healthy",
            "service": "psychic-tribble-api",
            "version": "1.0.0"
        }
    
    # Add metrics endpoint for monitoring
    @app.get("/metrics", tags=["Monitoring"])
    async def metrics():
        """Basic metrics endpoint."""
        return {
            "status": "ok",
            "metrics": {
                "requests_total": 0,  # Placeholder - would be implemented with proper metrics
                "errors_total": 0,
                "uptime": "0s"
            }
        }
    
    logger.info("Monitoring and metrics initialized")