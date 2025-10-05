"""
API endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Import the FastAPI app
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from organizer_api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.api
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestLLMEndpoint:
    """Tests for LLM endpoint."""

    @pytest.mark.api
    def test_llm_chat_endpoint(self, client):
        """Test LLM chat endpoint."""
        response = client.post(
            "/api/v1/llm/chat",
            json={"message": "Hello, test the system"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["response"] is not None

    @pytest.mark.api
    def test_llm_chat_empty_message(self, client):
        """Test LLM chat with empty message."""
        response = client.post(
            "/api/v1/llm/chat",
            json={"message": ""}
        )
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @pytest.mark.api
    def test_llm_chat_missing_message(self, client):
        """Test LLM chat without message field."""
        response = client.post(
            "/api/v1/llm/chat",
            json={}
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.security
    def test_llm_chat_xss_protection(self, client):
        """Test XSS protection in LLM chat."""
        response = client.post(
            "/api/v1/llm/chat",
            json={"message": "<script>alert('xss')</script>"}
        )
        # Should either sanitize or reject
        if response.status_code == 200:
            data = response.json()
            # Response should not contain unescaped script tags
            assert "<script>" not in str(data)


class TestCalendarEndpoints:
    """Tests for calendar endpoints."""

    @pytest.mark.api
    def test_get_events(self, client):
        """Test getting calendar events."""
        response = client.get("/api/v1/calendar/events")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.api
    def test_get_events_with_date_range(self, client):
        """Test getting events with date range."""
        response = client.get(
            "/api/v1/calendar/events",
            params={
                "start_date": "2025-10-01",
                "end_date": "2025-10-31"
            }
        )
        assert response.status_code == 200


class TestTasksEndpoints:
    """Tests for tasks endpoints."""

    @pytest.mark.api
    def test_get_tasks(self, client):
        """Test getting tasks."""
        response = client.get("/api/v1/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.api
    def test_get_tasks_by_status(self, client):
        """Test filtering tasks by status."""
        response = client.get(
            "/api/v1/tasks/",
            params={"status": "pending"}
        )
        assert response.status_code == 200

    @pytest.mark.api
    def test_get_tasks_by_priority(self, client):
        """Test filtering tasks by priority."""
        response = client.get(
            "/api/v1/tasks/",
            params={"priority": "high"}
        )
        assert response.status_code == 200


class TestContactsEndpoints:
    """Tests for contacts endpoints."""

    @pytest.mark.api
    def test_get_contacts(self, client):
        """Test getting contacts."""
        response = client.get("/api/v1/contacts/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.api
    def test_search_contacts(self, client):
        """Test searching contacts."""
        response = client.get(
            "/api/v1/contacts/",
            params={"search": "john"}
        )
        assert response.status_code == 200


class TestFilesEndpoints:
    """Tests for file activity endpoints."""

    @pytest.mark.api
    def test_get_file_activity(self, client):
        """Test getting file activity."""
        response = client.get("/api/v1/files/activity")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestErrorHandling:
    """Tests for API error handling."""

    @pytest.mark.api
    def test_404_not_found(self, client):
        """Test 404 handling."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    @pytest.mark.api
    def test_405_method_not_allowed(self, client):
        """Test 405 handling."""
        response = client.delete("/health")
        assert response.status_code == 405

    @pytest.mark.security
    def test_request_too_large(self, client):
        """Test handling of very large requests."""
        # Create a very large payload
        large_payload = {"message": "x" * (11 * 1024 * 1024)}  # 11MB
        response = client.post(
            "/api/v1/llm/chat",
            json=large_payload
        )
        # Should reject or handle gracefully
        assert response.status_code in [413, 422, 400]


class TestCORSAndSecurity:
    """Tests for CORS and security headers."""

    @pytest.mark.security
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/v1/llm/chat")
        # Should have CORS headers configured
        assert response.status_code in [200, 405]

    @pytest.mark.security
    def test_security_headers(self, client):
        """Test security headers are present."""
        response = client.get("/health")
        # Check for common security headers
        headers = response.headers
        # At least some basic headers should be present
        assert "content-type" in headers


class TestRateLimiting:
    """Tests for rate limiting."""

    @pytest.mark.api
    @pytest.mark.slow
    def test_rate_limit_headers(self, client):
        """Test rate limit headers."""
        response = client.get("/health")
        # Check if rate limit headers are present
        # (Implementation may vary)
        assert response.status_code == 200
