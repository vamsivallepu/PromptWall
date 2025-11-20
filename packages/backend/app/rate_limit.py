"""Rate limiting utilities"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def get_device_id(request: Request) -> str:
    """Extract device ID from request for rate limiting"""
    # Try to get device_id from request body (for POST requests)
    if hasattr(request.state, "device_id"):
        return request.state.device_id
    
    # Fallback to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_device_id,
    default_limits=["1000/hour"],
    storage_uri="memory://",
)
