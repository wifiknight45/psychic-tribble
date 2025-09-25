"""Enhanced monitoring and metrics setup."""
import logging
import time
from typing import Dict, Any
from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)

# Global metrics storage (in production, you'd use proper metrics backend)
_metrics = {
    "requests_total": 0,
    "requests_by_status": {},
    "requests_by_endpoint": {},
    "errors_total": 0,
    "start_time": time.time()
}


def init_metrics(app: FastAPI) -> None:
    """Initialize comprehensive application metrics and monitoring."""
    
    # Middleware to track request metrics
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        """Track request metrics."""
        start_time = time.time()
        
        # Increment total requests
        _metrics["requests_total"] += 1
        
        # Track requests by endpoint
        endpoint = request.url.path
        _metrics["requests_by_endpoint"][endpoint] = (
            _metrics["requests_by_endpoint"].get(endpoint, 0) + 1
        )
        
        response = await call_next(request)
        
        # Track response metrics
        status_code = response.status_code
        _metrics["requests_by_status"][status_code] = (
            _metrics["requests_by_status"].get(status_code, 0) + 1
        )
        
        # Track errors
        if status_code >= 400:
            _metrics["errors_total"] += 1
        
        # Add timing header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    # Enhanced health check endpoint
    @app.get("/health", tags=["Monitoring"], summary="Comprehensive health check")
    async def health_check(request: Request):
        """Comprehensive health check endpoint for monitoring systems."""
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Calculate uptime
        uptime_seconds = time.time() - _metrics["start_time"]
        uptime_hours = uptime_seconds / 3600
        
        health_data = {
            "status": "healthy",
            "service": "psychic-tribble-api",
            "version": "1.0.0",
            "environment": app.state.settings.ENV if hasattr(app.state, "settings") else "unknown",
            "request_id": request_id,
            "timestamp": time.time(),
            "uptime": {
                "seconds": uptime_seconds,
                "hours": uptime_hours,
                "human": f"{int(uptime_hours)}h {int((uptime_seconds % 3600) / 60)}m"
            },
            "checks": {
                "database": await _check_database(),
                "redis": await _check_redis(),
                "external_services": await _check_external_services()
            }
        }
        
        return health_data
    
    # Detailed metrics endpoint
    @app.get("/metrics", tags=["Monitoring"], summary="Application metrics")
    async def metrics_endpoint(request: Request):
        """Detailed metrics endpoint for monitoring and alerting."""
        request_id = getattr(request.state, "request_id", "unknown")
        
        current_time = time.time()
        uptime_seconds = current_time - _metrics["start_time"]
        
        metrics_data = {
            "timestamp": current_time,
            "request_id": request_id,
            "service": "psychic-tribble-api",
            "version": "1.0.0",
            "uptime_seconds": uptime_seconds,
            "metrics": {
                "requests": {
                    "total": _metrics["requests_total"],
                    "by_status": _metrics["requests_by_status"],
                    "by_endpoint": _metrics["requests_by_endpoint"],
                    "errors_total": _metrics["errors_total"],
                    "error_rate": (
                        _metrics["errors_total"] / max(_metrics["requests_total"], 1) * 100
                    )
                },
                "system": {
                    "uptime_seconds": uptime_seconds,
                    # In production, add memory usage, CPU, etc.
                }
            }
        }
        
        return metrics_data
    
    # Readiness probe for Kubernetes/container orchestration
    @app.get("/ready", tags=["Monitoring"], summary="Readiness probe")
    async def readiness_check():
        """Readiness probe to check if service is ready to accept traffic."""
        # Check critical dependencies
        db_healthy = await _check_database()
        
        if not db_healthy:
            return {"status": "not_ready", "reason": "database_unavailable"}, 503
        
        return {"status": "ready"}
    
    # Liveness probe for Kubernetes/container orchestration
    @app.get("/live", tags=["Monitoring"], summary="Liveness probe")
    async def liveness_check():
        """Liveness probe to check if service is alive."""
        return {"status": "alive", "timestamp": time.time()}
    
    logger.info("Enhanced monitoring and metrics initialized")


async def _check_database() -> bool:
    """Check database connectivity."""
    # Placeholder - implement actual database health check
    # In real implementation:
    # try:
    #     await database.execute("SELECT 1")
    #     return True
    # except Exception:
    #     return False
    return True


async def _check_redis() -> bool:
    """Check Redis connectivity."""
    # Placeholder - implement actual Redis health check
    # In real implementation:
    # try:
    #     await redis.ping()
    #     return True
    # except Exception:
    #     return False
    return True


async def _check_external_services() -> Dict[str, Any]:
    """Check external service dependencies."""
    # Placeholder - implement actual external service checks
    return {
        "vault": True,  # HashiCorp Vault
        "email_service": True,
        "third_party_apis": True
    }