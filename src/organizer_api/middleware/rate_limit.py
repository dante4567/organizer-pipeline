"""
Rate limiting middleware for API protection.
"""

import time
from typing import Dict, Callable
from collections import defaultdict, deque
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from organizer_core.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse."""

    def __init__(self, app):
        super().__init__(app)
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.settings = get_settings()

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, handling proxies."""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct connection
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited."""
        now = time.time()
        window_start = now - 60  # 1 minute window

        # Clean old requests
        while self.requests[client_ip] and self.requests[client_ip][0] < window_start:
            self.requests[client_ip].popleft()

        # Check rate limit
        current_requests = len(self.requests[client_ip])
        limit = self.settings.security.rate_limit_per_minute

        if current_requests >= limit:
            return True

        # Add current request
        self.requests[client_ip].append(now)
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting."""
        client_ip = self._get_client_ip(request)

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Check if client is whitelisted (localhost)
        if client_ip.startswith(("127.0.0.1", "::1", "localhost")):
            return await call_next(request)

        # Apply rate limiting
        if self._is_rate_limited(client_ip):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.settings.security.rate_limit_per_minute} requests per minute",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )

        response = await call_next(request)

        # Add rate limit headers
        current_requests = len(self.requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.settings.security.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.settings.security.rate_limit_per_minute - current_requests)
        )
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))

        return response