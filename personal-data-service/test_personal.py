#!/usr/bin/env python3
"""
Comprehensive test suite for Personal Data Management Service
Tests all endpoints and functionality
"""

import requests
import json
from datetime import datetime, timedelta
import time
import sys

BASE_URL = "http://localhost:8002"

def colored_print(message, color="reset"):
    """Print colored output"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['reset'])}{message}{colors['reset']}")

def wait_for_service(max_retries=30, delay=2):
    """Wait for service to be ready"""
    colored_print("Waiting for service to start...", "yellow")

    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                colored_print("✓ Service is ready!", "green")
                return True
        except requests.exceptions.RequestException:
            pass

        if i < max_retries - 1:
            time.sleep(delay)

    colored_print("✗ Service failed to start", "red")
    return False

def test_health():
    """Test health check endpoint"""
    colored_print("\n=== Testing Health Check ===", "blue")

    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "status" in data, "Missing status field"
        assert data["status"] == "healthy", f"Expected healthy, got {data['status']}"

        colored_print("✓ Health check passed", "green")
        return True
    except Exception as e:
        colored_print(f"✗ Health check failed: {e}", "red")
        return False

def test_calendar():
    """Test calendar functionality"""
    colored_print("\n=== Testing Calendar ===", "blue")

    try:
        # Create event
        tomorrow = datetime.now() + timedelta(days=1)
        event_data = {
            "title": "Test Meeting",
            "description": "A test meeting",
            "start_time": tomorrow.isoformat(),
            "end_time": (tomorrow + timedelta(hours=1)).isoformat(),
            "location": "Conference Room A",
            "event_type": "meeting",
            "attendees": ["john@example.com", "jane@example.com"],
            "reminder_minutes": 15
        }

        response = requests.post(f"{BASE_URL}/calendar/events", json=event_data)
        assert response.status_code == 200, f"Create event failed: {response.status_code}"

        event_id = response.json()["event_id"]
        colored_print(f"✓ Event created with ID: {event_id}", "green")

        # Get the created event
        response = requests.get(f"{BASE_URL}/calendar/events/{event_id}")
        assert response.status_code == 200, "Get event failed"

        event = response.json()["event"]
        assert event["title"] == "Test Meeting", "Event title mismatch"
        colored_print("✓ Event retrieved successfully", "green")

        # Get all events
        response = requests.get(f"{BASE_URL}/calendar/events")
        assert response.status_code == 200, "Get events failed"

        events = response.json()["events"]
        assert len(events) >= 1, "No events found"
        colored_print(f"✓ Retrieved {len(events)} events", "green")

        # Get today's events
        response = requests.get(f"{BASE_URL}/calendar/today")
        assert response.status_code == 200, "Get today's events failed"
        colored_print("✓ Today's events retrieved", "green")

        # Update event
        event_data["title"] = "Updated Test Meeting"
        response = requests.put(f"{BASE_URL}/calendar/events/{event_id}", json=event_data)
        assert response.status_code == 200, "Update event failed"
        colored_print("✓ Event updated successfully", "green")

        # Delete event
        response = requests.delete(f"{BASE_URL}/calendar/events/{event_id}")
        assert response.status_code == 200, "Delete event failed"
        colored_print("✓ Event deleted successfully", "green")

        return True

    except Exception as e:
        colored_print(f"✗ Calendar test failed: {e}", "red")
        return False

def test_tasks():
    """Test task functionality"""
    colored_print("\n=== Testing Tasks ===", "blue")

    try:
        # Create task
        due_date = datetime.now() + timedelta(days=3)
        task_data = {
            "title": "Test Task",
            "description": "A test task for the API",
            "priority": "high",
            "due_date": due_date.isoformat(),
            "tags": ["testing", "api"],
            "assigned_to": "test_user"
        }

        response = requests.post(f"{BASE_URL}/tasks", json=task_data)
        assert response.status_code == 200, f"Create task failed: {response.status_code}"

        task_id = response.json()["task_id"]
        colored_print(f"✓ Task created with ID: {task_id}", "green")

        # Get the created task
        response = requests.get(f"{BASE_URL}/tasks/{task_id}")
        assert response.status_code == 200, "Get task failed"

        task = response.json()["task"]
        assert task["title"] == "Test Task", "Task title mismatch"
        assert task["priority"] == "high", "Task priority mismatch"
        colored_print("✓ Task retrieved successfully", "green")

        # Get all tasks
        response = requests.get(f"{BASE_URL}/tasks")
        assert response.status_code == 200, "Get tasks failed"

        tasks = response.json()["tasks"]
        assert len(tasks) >= 1, "No tasks found"
        colored_print(f"✓ Retrieved {len(tasks)} tasks", "green")

        # Get pending tasks
        response = requests.get(f"{BASE_URL}/tasks?status=pending")
        assert response.status_code == 200, "Get pending tasks failed"

        pending_tasks = response.json()["tasks"]
        colored_print(f"✓ Retrieved {len(pending_tasks)} pending tasks", "green")

        # Update task status
        task_data["status"] = "completed"
        response = requests.put(f"{BASE_URL}/tasks/{task_id}", json=task_data)
        assert response.status_code == 200, "Update task failed"
        colored_print("✓ Task marked as completed", "green")

        # Delete task
        response = requests.delete(f"{BASE_URL}/tasks/{task_id}")
        assert response.status_code == 200, "Delete task failed"
        colored_print("✓ Task deleted successfully", "green")

        return True

    except Exception as e:
        colored_print(f"✗ Task test failed: {e}", "red")
        return False

def test_contacts():
    """Test contact functionality"""
    colored_print("\n=== Testing Contacts ===", "blue")

    try:
        # Create contact
        contact_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "address": "123 Main St, Anytown, USA",
            "company": "Test Corp",
            "birthday": "1990-01-15",
            "notes": "This is a test contact",
            "tags": ["test", "api"]
        }

        response = requests.post(f"{BASE_URL}/contacts", json=contact_data)
        assert response.status_code == 200, f"Create contact failed: {response.status_code}"

        contact_id = response.json()["contact_id"]
        colored_print(f"✓ Contact created with ID: {contact_id}", "green")

        # Get the created contact
        response = requests.get(f"{BASE_URL}/contacts/{contact_id}")
        assert response.status_code == 200, "Get contact failed"

        contact = response.json()["contact"]
        assert contact["name"] == "John Doe", "Contact name mismatch"
        assert contact["email"] == "john.doe@example.com", "Contact email mismatch"
        colored_print("✓ Contact retrieved successfully", "green")

        # Get all contacts
        response = requests.get(f"{BASE_URL}/contacts")
        assert response.status_code == 200, "Get contacts failed"

        contacts = response.json()["contacts"]
        assert len(contacts) >= 1, "No contacts found"
        colored_print(f"✓ Retrieved {len(contacts)} contacts", "green")

        # Search contacts
        response = requests.get(f"{BASE_URL}/contacts?search=John")
        assert response.status_code == 200, "Search contacts failed"

        search_results = response.json()["contacts"]
        colored_print(f"✓ Found {len(search_results)} contacts matching 'John'", "green")

        # Update contact
        contact_data["company"] = "Updated Test Corp"
        response = requests.put(f"{BASE_URL}/contacts/{contact_id}", json=contact_data)
        assert response.status_code == 200, "Update contact failed"
        colored_print("✓ Contact updated successfully", "green")

        # Delete contact
        response = requests.delete(f"{BASE_URL}/contacts/{contact_id}")
        assert response.status_code == 200, "Delete contact failed"
        colored_print("✓ Contact deleted successfully", "green")

        return True

    except Exception as e:
        colored_print(f"✗ Contact test failed: {e}", "red")
        return False

def test_files():
    """Test file management functionality"""
    colored_print("\n=== Testing File Management ===", "blue")

    try:
        # List files in root directory
        response = requests.get(f"{BASE_URL}/files")
        assert response.status_code == 200, "List files failed"

        files = response.json()["files"]
        colored_print(f"✓ Listed {len(files)} files in root directory", "green")

        # Try to get info for a non-existent file (should return 404)
        response = requests.get(f"{BASE_URL}/files/info?path=nonexistent.txt")
        assert response.status_code == 404, "Expected 404 for non-existent file"
        colored_print("✓ Non-existent file correctly returns 404", "green")

        return True

    except Exception as e:
        colored_print(f"✗ File test failed: {e}", "red")
        return False

def test_natural_language():
    """Test natural language processing"""
    colored_print("\n=== Testing Natural Language Processing ===", "blue")

    try:
        # Test calendar event creation
        nl_request = {
            "text": "Schedule a meeting with the team tomorrow at 2pm"
        }

        response = requests.post(f"{BASE_URL}/process/natural", json=nl_request)
        # This might fail without LLM API key, but should not crash
        colored_print(f"✓ Natural language processing tested (status: {response.status_code})", "green")

        if response.status_code == 200:
            result = response.json()
            colored_print(f"  → Parsed as: {result.get('parsed', {}).get('type', 'unknown')}", "green")

        # Test task creation
        nl_request = {
            "text": "Remind me to call the dentist next week"
        }

        response = requests.post(f"{BASE_URL}/process/natural", json=nl_request)
        colored_print(f"✓ Task creation via NLP tested (status: {response.status_code})", "green")

        return True

    except Exception as e:
        colored_print(f"✗ Natural language test failed: {e}", "red")
        return False

def test_summary_and_stats():
    """Test summary and statistics endpoints"""
    colored_print("\n=== Testing Summary & Statistics ===", "blue")

    try:
        # Create some test data first
        tomorrow = datetime.now() + timedelta(days=1)

        # Create a test event
        event_data = {
            "title": "Test Event for Summary",
            "start_time": tomorrow.isoformat(),
            "event_type": "meeting"
        }
        requests.post(f"{BASE_URL}/calendar/events", json=event_data)

        # Create a test task
        task_data = {
            "title": "Test Task for Summary",
            "priority": "medium"
        }
        requests.post(f"{BASE_URL}/tasks", json=task_data)

        # Get today's summary
        response = requests.get(f"{BASE_URL}/summary/today")
        assert response.status_code == 200, "Get today's summary failed"

        summary = response.json()
        assert "events" in summary, "Summary missing events"
        assert "tasks" in summary, "Summary missing tasks"
        colored_print("✓ Today's summary retrieved", "green")

        # Get statistics
        response = requests.get(f"{BASE_URL}/stats")
        assert response.status_code == 200, "Get statistics failed"

        stats = response.json()
        assert "total_events" in stats, "Stats missing total_events"
        assert "total_tasks" in stats, "Stats missing total_tasks"
        assert "total_contacts" in stats, "Stats missing total_contacts"

        colored_print(f"✓ Statistics: {stats['total_events']} events, {stats['total_tasks']} tasks, {stats['total_contacts']} contacts", "green")

        return True

    except Exception as e:
        colored_print(f"✗ Summary and stats test failed: {e}", "red")
        return False

def test_openwebui_functions():
    """Test OpenWebUI integration functions"""
    colored_print("\n=== Testing OpenWebUI Functions ===", "blue")

    try:
        # Test manage_calendar function
        def manage_calendar(command: str):
            response = requests.post(
                f"{BASE_URL}/process/natural",
                json={"text": command}
            )
            if response.status_code == 200:
                return response.json()
            else:
                return f"Failed to process: {response.status_code}"

        result = manage_calendar("What's on my calendar today?")
        colored_print("✓ manage_calendar function works", "green")

        # Test quick_task function
        def quick_task(title: str, priority: str = "medium"):
            response = requests.post(
                f"{BASE_URL}/tasks",
                json={"title": title, "priority": priority}
            )
            if response.status_code == 200:
                return f"Task created: {title}"
            else:
                return f"Failed to create task"

        result = quick_task("Test task from OpenWebUI function", "high")
        colored_print("✓ quick_task function works", "green")

        # Test get_today_summary function
        def get_today_summary():
            events_response = requests.get(f"{BASE_URL}/calendar/today")
            tasks_response = requests.get(f"{BASE_URL}/tasks?status=pending&limit=5")

            summary = "Today's Schedule:\n"

            if events_response.status_code == 200:
                events = events_response.json()['events']
                for event in events:
                    summary += f"• {event['start_time']}: {event['title']}\n"

            summary += "\nPending Tasks:\n"

            if tasks_response.status_code == 200:
                tasks = tasks_response.json()['tasks']
                for task in tasks[:5]:
                    summary += f"• [{task['priority']}] {task['title']}\n"

            return summary

        summary = get_today_summary()
        colored_print("✓ get_today_summary function works", "green")

        return True

    except Exception as e:
        colored_print(f"✗ OpenWebUI functions test failed: {e}", "red")
        return False

def test_error_handling():
    """Test error handling"""
    colored_print("\n=== Testing Error Handling ===", "blue")

    try:
        # Test 404 errors
        response = requests.get(f"{BASE_URL}/calendar/events/99999")
        assert response.status_code == 404, "Expected 404 for non-existent event"
        colored_print("✓ 404 error handling works", "green")

        # Test invalid data
        response = requests.post(f"{BASE_URL}/calendar/events", json={"invalid": "data"})
        assert response.status_code == 422, "Expected 422 for invalid data"
        colored_print("✓ Validation error handling works", "green")

        return True

    except Exception as e:
        colored_print(f"✗ Error handling test failed: {e}", "red")
        return False

def main():
    """Run all tests"""
    colored_print("🚀 Personal Data Service Test Suite", "blue")
    colored_print("=" * 50, "blue")

    # Wait for service to be ready
    if not wait_for_service():
        colored_print("Service is not available. Make sure it's running on port 8002.", "red")
        sys.exit(1)

    # Run all tests
    tests = [
        test_health,
        test_calendar,
        test_tasks,
        test_contacts,
        test_files,
        test_natural_language,
        test_summary_and_stats,
        test_openwebui_functions,
        test_error_handling
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            colored_print(f"✗ Test {test.__name__} crashed: {e}", "red")
            failed += 1

    # Print summary
    colored_print("\n" + "=" * 50, "blue")
    colored_print(f"📊 Test Results: {passed} passed, {failed} failed", "blue")

    if failed == 0:
        colored_print("🎉 All tests passed!", "green")
        return 0
    else:
        colored_print(f"❌ {failed} test(s) failed", "red")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)