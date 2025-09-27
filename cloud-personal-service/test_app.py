"""
Comprehensive test suite for Cloud Personal Data Service
"""
import pytest
import asyncio
import json
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

# Import the app
from app import app, get_llm_service, init_database

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing"""
    service = MagicMock()
    service.generate_response = AsyncMock()
    service.get_cost_for_operation = MagicMock(return_value=0.001)
    service.get_total_costs = MagicMock(return_value={
        "total": 1.50,
        "by_provider": {"anthropic": 0.80, "openai": 0.50, "groq": 0.20},
        "by_operation": {"intent_parsing": 0.30, "date_parsing": 0.40, "task_generation": 0.80}
    })
    return service

@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database"""
    # Use in-memory database for tests
    os.environ["DB_PATH"] = ":memory:"
    init_database()
    yield
    # Cleanup after test
    if "DB_PATH" in os.environ:
        del os.environ["DB_PATH"]

class TestHealthEndpoints:
    """Test health and status endpoints"""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "services" in data
        assert "database" in data["services"]
        assert "llm" in data["services"]

    def test_stats_endpoint(self, client):
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        required_fields = [
            "total_events", "today_events", "total_tasks",
            "pending_tasks", "total_contacts", "generated_at"
        ]
        for field in required_fields:
            assert field in data

class TestTaskEndpoints:
    """Test task management endpoints"""

    def test_create_task_basic(self, client):
        task_data = {
            "title": "Test task",
            "priority": "medium"
        }
        response = client.post("/tasks", json=task_data)
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["title"] == "Test task"

    def test_create_task_with_due_date(self, client):
        future_date = (datetime.now() + timedelta(days=7)).isoformat()
        task_data = {
            "title": "Task with due date",
            "priority": "high",
            "due_date": future_date
        }
        response = client.post("/tasks", json=task_data)
        assert response.status_code == 200
        data = response.json()
        assert data["due_date"] is not None

    def test_get_tasks(self, client):
        # Create a test task first
        task_data = {"title": "Test task", "priority": "low"}
        client.post("/tasks", json=task_data)

        response = client.get("/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert len(data["tasks"]) >= 1

    def test_get_tasks_with_filters(self, client):
        # Create tasks with different statuses
        client.post("/tasks", json={"title": "Pending task", "priority": "medium"})

        response = client.get("/tasks?status=pending&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

    def test_update_task_status(self, client):
        # Create task
        task_data = {"title": "Task to update", "priority": "medium"}
        create_response = client.post("/tasks", json=task_data)
        task_id = create_response.json()["task_id"]

        # Update status
        update_data = {"status": "completed"}
        response = client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

class TestContactEndpoints:
    """Test contact management endpoints"""

    def test_create_contact(self, client):
        contact_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890"
        }
        response = client.post("/contacts", json=contact_data)
        assert response.status_code == 200
        data = response.json()
        assert "contact_id" in data
        assert data["name"] == "John Doe"

    def test_get_contacts(self, client):
        # Create a test contact first
        contact_data = {"name": "Jane Doe", "email": "jane@example.com"}
        client.post("/contacts", json=contact_data)

        response = client.get("/contacts")
        assert response.status_code == 200
        data = response.json()
        assert "contacts" in data

    def test_search_contacts(self, client):
        # Create test contacts
        contacts = [
            {"name": "Alice Smith", "email": "alice@company.com", "company": "TechCorp"},
            {"name": "Bob Johnson", "email": "bob@example.com", "company": "StartupInc"}
        ]
        for contact in contacts:
            client.post("/contacts", json=contact)

        response = client.get("/contacts?search=TechCorp")
        assert response.status_code == 200
        data = response.json()
        assert "contacts" in data

class TestCalendarEndpoints:
    """Test calendar management endpoints"""

    def test_create_event(self, client):
        start_time = (datetime.now() + timedelta(hours=1)).isoformat()
        end_time = (datetime.now() + timedelta(hours=2)).isoformat()

        event_data = {
            "title": "Test Meeting",
            "start_time": start_time,
            "end_time": end_time,
            "event_type": "meeting"
        }
        response = client.post("/calendar/events", json=event_data)
        assert response.status_code == 200
        data = response.json()
        assert "event_id" in data
        assert data["title"] == "Test Meeting"

    def test_get_today_events(self, client):
        response = client.get("/calendar/today")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data

    def test_get_events_date_range(self, client):
        start_date = datetime.now().date().isoformat()
        end_date = (datetime.now() + timedelta(days=7)).date().isoformat()

        response = client.get(f"/calendar/events?start_date={start_date}&end_date={end_date}")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data

class TestLLMIntegration:
    """Test LLM integration and natural language processing"""

    @patch('app.get_llm_service')
    def test_natural_language_processing(self, mock_get_service, client):
        # Mock the LLM service
        mock_service = MagicMock()
        mock_service.generate_response = AsyncMock(return_value={
            "action": "create_task",
            "parameters": {"title": "Buy groceries", "priority": "medium"},
            "confidence": 0.9,
            "reasoning": "User wants to create a task to buy groceries"
        })
        mock_get_service.return_value = mock_service

        response = client.post("/process/natural", json={"text": "I need to buy groceries"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    @patch('app.get_llm_service')
    def test_intent_parsing(self, mock_get_service, client):
        mock_service = MagicMock()
        mock_service.generate_response = AsyncMock(return_value={
            "intent": "schedule_meeting",
            "entities": {
                "title": "Team standup",
                "date": "2024-01-15",
                "time": "10:00"
            },
            "confidence": 0.95
        })
        mock_get_service.return_value = mock_service

        response = client.post("/llm/parse-intent", json={
            "text": "Schedule team standup for January 15th at 10am"
        })
        assert response.status_code == 200
        data = response.json()
        assert "intent" in data

class TestCostTracking:
    """Test cost tracking and analytics"""

    @patch('app.get_llm_service')
    def test_cost_analytics(self, mock_get_service, client):
        mock_service = MagicMock()
        mock_service.get_total_costs = MagicMock(return_value={
            "total": 5.75,
            "by_provider": {"anthropic": 3.25, "openai": 1.50, "groq": 1.00},
            "by_operation": {"intent_parsing": 2.00, "date_parsing": 1.75, "task_generation": 2.00}
        })
        mock_get_service.return_value = mock_service

        response = client.get("/analytics/costs")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_provider" in data
        assert "by_operation" in data

    @patch('app.get_llm_service')
    def test_daily_cost_summary(self, mock_get_service, client):
        mock_service = MagicMock()
        mock_service.get_daily_costs = MagicMock(return_value={
            "date": datetime.now().date().isoformat(),
            "total_cost": 2.50,
            "requests": 45,
            "average_cost_per_request": 0.056
        })
        mock_get_service.return_value = mock_service

        response = client.get("/analytics/costs/daily")
        assert response.status_code == 200
        data = response.json()
        assert "total_cost" in data

class TestFileOperations:
    """Test file upload and management"""

    def test_file_upload(self, client):
        # Create a test file
        test_content = b"This is test file content"
        files = {"file": ("test.txt", test_content, "text/plain")}

        response = client.post("/files/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data
        assert data["filename"] == "test.txt"

    def test_list_files(self, client):
        response = client.get("/files/")
        assert response.status_code == 200
        data = response.json()
        assert "files" in data

class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_task_creation(self, client):
        # Missing required fields
        response = client.post("/tasks", json={})
        assert response.status_code == 422

    def test_nonexistent_task_update(self, client):
        response = client.put("/tasks/999999", json={"status": "completed"})
        assert response.status_code == 404

    def test_invalid_date_format(self, client):
        event_data = {
            "title": "Test Event",
            "start_time": "invalid-date",
            "end_time": "also-invalid",
            "event_type": "meeting"
        }
        response = client.post("/calendar/events", json=event_data)
        assert response.status_code == 422

class TestRealLLMIntegration:
    """Test real LLM API integration (requires API keys)"""

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY"),
        reason="No LLM API keys available"
    )
    def test_real_llm_call(self, client):
        """Test with real LLM API (only runs if API keys are available)"""
        response = client.post("/llm/parse-intent", json={
            "text": "Remind me to call mom tomorrow at 3pm"
        })
        assert response.status_code == 200
        data = response.json()
        assert "intent" in data

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY"),
        reason="No LLM API keys available"
    )
    def test_real_natural_processing(self, client):
        """Test natural language processing with real LLM"""
        response = client.post("/process/natural", json={
            "text": "Create a high priority task to finish the project report by Friday"
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])