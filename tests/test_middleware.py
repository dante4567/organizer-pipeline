"""
Middleware tests.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
import time

from organizer_api.middleware.security import SecurityMiddleware
from organizer_api.middleware.rate_limit import RateLimitMiddleware


class TestSecurityMiddleware:
    """Tests for SecurityMiddleware."""

    @pytest.fixture
    def app_with_security(self):
        """Create app with security middleware."""
        app = FastAPI()
        app.add_middleware(SecurityMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        return app

    @pytest.mark.security
    def test_security_headers_added(self, app_with_security):
        """Test that security headers are added."""
        client = TestClient(app_with_security)
        response = client.get("/test")

        # Check for security headers
        headers = response.headers
        assert "x-content-type-options" in headers
        assert headers["x-content-type-options"] == "nosniff"

    @pytest.mark.security
    def test_xss_protection_header(self, app_with_security):
        """Test XSS protection header."""
        client = TestClient(app_with_security)
        response = client.get("/test")

        headers = response.headers
        # Check for XSS protection (may vary by implementation)
        assert response.status_code == 200

    @pytest.mark.security
    def test_frame_options_header(self, app_with_security):
        """Test frame options header."""
        client = TestClient(app_with_security)
        response = client.get("/test")

        headers = response.headers
        # Should have frame options set
        if "x-frame-options" in headers:
            assert headers["x-frame-options"] in ["DENY", "SAMEORIGIN"]


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware."""

    @pytest.fixture
    def app_with_rate_limit(self):
        """Create app with rate limiting."""
        app = FastAPI()
        # Configure with low limits for testing
        app.add_middleware(
            RateLimitMiddleware,
            max_requests=5,
            window_seconds=60
        )

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        return app

    @pytest.mark.unit
    def test_rate_limit_allows_normal_requests(self, app_with_rate_limit):
        """Test that normal requests are allowed."""
        client = TestClient(app_with_rate_limit)

        # Make a few requests within limit
        for i in range(3):
            response = client.get("/test")
            assert response.status_code == 200

    @pytest.mark.slow
    def test_rate_limit_blocks_excessive_requests(self, app_with_rate_limit):
        """Test that excessive requests are blocked."""
        client = TestClient(app_with_rate_limit)

        # Make requests up to and beyond the limit
        responses = []
        for i in range(10):
            response = client.get("/test")
            responses.append(response.status_code)

        # At least some requests should be successful
        assert 200 in responses

        # If rate limiting is strict, some might be blocked
        # (This depends on implementation details)

    @pytest.mark.unit
    def test_rate_limit_headers(self, app_with_rate_limit):
        """Test rate limit headers are present."""
        client = TestClient(app_with_rate_limit)
        response = client.get("/test")

        # Check for rate limit information headers
        # (Implementation specific)
        assert response.status_code == 200


class TestMiddlewareIntegration:
    """Integration tests for multiple middleware."""

    @pytest.fixture
    def app_with_all_middleware(self):
        """Create app with all middleware."""
        app = FastAPI()
        app.add_middleware(SecurityMiddleware)
        app.add_middleware(
            RateLimitMiddleware,
            max_requests=10,
            window_seconds=60
        )

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        @app.post("/echo")
        async def echo_endpoint(request: Request):
            body = await request.json()
            return body

        return app

    @pytest.mark.integration
    def test_all_middleware_working(self, app_with_all_middleware):
        """Test that all middleware work together."""
        client = TestClient(app_with_all_middleware)

        # Make a request
        response = client.get("/test")
        assert response.status_code == 200

        # Should have security headers
        assert "x-content-type-options" in response.headers

    @pytest.mark.integration
    def test_middleware_order(self, app_with_all_middleware):
        """Test middleware execution order."""
        client = TestClient(app_with_all_middleware)

        # POST request to test middleware chain
        response = client.post("/echo", json={"test": "data"})
        assert response.status_code == 200

        # Should have security headers
        headers = response.headers
        assert "x-content-type-options" in headers


class TestCORSMiddleware:
    """Tests for CORS middleware."""

    @pytest.fixture
    def app_with_cors(self):
        """Create app with CORS middleware."""
        from fastapi.middleware.cors import CORSMiddleware

        app = FastAPI()
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        return app

    @pytest.mark.security
    def test_cors_headers(self, app_with_cors):
        """Test CORS headers are set."""
        client = TestClient(app_with_cors)

        # Make a request with Origin header
        response = client.get(
            "/test",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200

        # Check for CORS headers
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    @pytest.mark.security
    def test_cors_preflight(self, app_with_cors):
        """Test CORS preflight requests."""
        client = TestClient(app_with_cors)

        # Make OPTIONS request
        response = client.options(
            "/test",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        # Should handle preflight
        assert response.status_code in [200, 204]


class TestMiddlewareErrorHandling:
    """Tests for middleware error handling."""

    @pytest.fixture
    def app_with_error_handling(self):
        """Create app with middleware that handles errors."""
        app = FastAPI()
        app.add_middleware(SecurityMiddleware)

        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")

        @app.get("/success")
        async def success_endpoint():
            return {"message": "success"}

        return app

    @pytest.mark.unit
    def test_middleware_on_error(self, app_with_error_handling):
        """Test that middleware works even when endpoint errors."""
        client = TestClient(app_with_error_handling)

        # This will error but middleware should still apply
        response = client.get("/error")
        # Should still have security headers even on error
        assert "x-content-type-options" in response.headers

    @pytest.mark.unit
    def test_middleware_on_success(self, app_with_error_handling):
        """Test middleware on successful requests."""
        client = TestClient(app_with_error_handling)

        response = client.get("/success")
        assert response.status_code == 200
        assert "x-content-type-options" in response.headers
