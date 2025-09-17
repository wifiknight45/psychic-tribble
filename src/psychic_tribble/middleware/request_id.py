"""Request ID middleware for correlation tracking."""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request IDs for correlation tracking."""
    
    async def dispatch(self, request: Request, call_next):
        """Add request ID to request state and response headers."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Store in request state for use throughout the request lifecycle
        request.state.request_id = request_id
        
        # Process the request
        response: Response = await call_next(request)
        
        # Add request ID to response headers for client correlation
        response.headers["X-Request-ID"] = request_id
        
        return response