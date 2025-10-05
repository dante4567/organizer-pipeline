"""
Validation middleware for FastAPI integration.
"""

from fastapi import Request, HTTPException
from typing import Callable
import time


class ValidationMiddleware:
    """Middleware for automatic request validation."""

    def __init__(self, app):
        """
        Initialize validation middleware.

        Args:
            app: FastAPI application instance
        """
        self.app = app

    async def __call__(self, scope, receive, send):
        """
        ASGI middleware handler.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Validate request
        request = Request(scope, receive)

        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            if int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                await self._send_error(send, 413, "Request too large")
                return

        # Continue processing
        await self.app(scope, receive, send)

    async def _send_error(self, send: Callable, status_code: int, message: str):
        """
        Send error response.

        Args:
            send: ASGI send callable
            status_code: HTTP status code
            message: Error message
        """
        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": f'{{"error": "{message}"}}'.encode(),
        })


def validate_request_size(max_size: int = 10 * 1024 * 1024):
    """
    Decorator to validate request body size.

    Args:
        max_size: Maximum allowed size in bytes (default 10MB)

    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > max_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"Request body too large (max {max_size} bytes)"
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
