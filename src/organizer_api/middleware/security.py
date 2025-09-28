"""
Security middleware for FastAPI application.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from organizer_core.config.security import SecurityConfig


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware to add security headers and protections."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to all responses."""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = SecurityConfig.create_content_security_policy()

        # Remove server header
        if "server" in response.headers:
            del response.headers["server"]

        # Add custom headers
        response.headers["X-API-Version"] = "2.0.0"
        response.headers["X-Response-Time"] = str(int(time.time() * 1000))

        return response