"""
Pytest configuration and fixtures for the test suite.
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator
from datetime import datetime, timezone

# Set test environment variables
os.environ.setdefault('LLM_PROVIDER', 'demo')
os.environ.setdefault('LLM_MODEL', 'demo')
os.environ.setdefault('SECURITY_SECRET_KEY', 'test-secret-key-for-testing-only-32chars')
os.environ.setdefault('ENVIRONMENT', 'test')


@pytest.fixture
def sample_datetime():
    """Provide a sample datetime for testing."""
    return datetime(2025, 10, 5, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_event_data(sample_datetime):
    """Provide sample calendar event data."""
    return {
        "title": "Test Meeting",
        "start_time": sample_datetime,
        "description": "A test meeting",
        "location": "Conference Room A"
    }


@pytest.fixture
def sample_task_data():
    """Provide sample task data."""
    return {
        "title": "Test Task",
        "description": "A test task to complete",
        "priority": "high",
        "tags": ["work", "urgent"]
    }


@pytest.fixture
def sample_contact_data():
    """Provide sample contact data."""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "notes": "Test contact"
    }


@pytest.fixture
async def demo_provider():
    """Provide a demo LLM provider for testing."""
    from organizer_core.providers import create_llm_provider
    provider = create_llm_provider("demo", {"model": "demo"})
    return provider


@pytest.fixture
def settings():
    """Provide test settings."""
    from organizer_core.config import get_settings
    return get_settings()
