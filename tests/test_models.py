"""
Unit tests for organizer_core data models.
"""

import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from organizer_core.models import (
    CalendarEvent,
    TodoItem,
    Contact,
    FileActivity
)


class TestCalendarEvent:
    """Tests for CalendarEvent model."""

    @pytest.mark.unit
    def test_create_event(self, sample_event_data):
        """Test creating a calendar event."""
        event = CalendarEvent(**sample_event_data)
        assert event.title == "Test Meeting"
        assert event.description == "A test meeting"
        assert event.location == "Conference Room A"
        assert event.start_time is not None

    @pytest.mark.unit
    def test_event_requires_title(self, sample_datetime):
        """Test that title is required."""
        with pytest.raises(ValidationError):
            CalendarEvent(
                start_time=sample_datetime,
                description="No title"
            )

    @pytest.mark.unit
    def test_event_requires_start_time(self):
        """Test that start_time is required."""
        with pytest.raises(ValidationError):
            CalendarEvent(
                title="No start time",
                description="Missing start time"
            )

    @pytest.mark.unit
    def test_event_with_end_time(self, sample_datetime):
        """Test event with end time."""
        end_time = sample_datetime + timedelta(hours=1)
        event = CalendarEvent(
            title="Meeting",
            start_time=sample_datetime,
            end_time=end_time
        )
        assert event.end_time == end_time
        assert event.end_time > event.start_time

    @pytest.mark.unit
    def test_event_all_day(self, sample_datetime):
        """Test all-day event."""
        event = CalendarEvent(
            title="All Day Event",
            start_time=sample_datetime,
            all_day=True
        )
        assert event.all_day is True


class TestTodoItem:
    """Tests for TodoItem model."""

    @pytest.mark.unit
    def test_create_task(self, sample_task_data):
        """Test creating a task."""
        task = TodoItem(**sample_task_data)
        assert task.title == "Test Task"
        assert task.priority == "high"
        assert "work" in task.tags

    @pytest.mark.unit
    def test_task_requires_title(self):
        """Test that title is required."""
        with pytest.raises(ValidationError):
            TodoItem(description="No title")

    @pytest.mark.unit
    def test_task_default_status(self):
        """Test default status is pending."""
        task = TodoItem(title="New Task")
        assert task.status == "pending"

    @pytest.mark.unit
    def test_task_priority_validation(self):
        """Test priority validation."""
        # Valid priorities
        for priority in ["low", "medium", "high", "urgent"]:
            task = TodoItem(title="Task", priority=priority)
            assert task.priority == priority

    @pytest.mark.unit
    def test_task_with_due_date(self, sample_datetime):
        """Test task with due date."""
        task = TodoItem(
            title="Task with deadline",
            due_date=sample_datetime
        )
        assert task.due_date == sample_datetime


class TestContact:
    """Tests for Contact model."""

    @pytest.mark.unit
    def test_create_contact(self, sample_contact_data):
        """Test creating a contact."""
        contact = Contact(**sample_contact_data)
        assert contact.name == "John Doe"
        assert contact.email == "john.doe@example.com"
        assert contact.phone == "+1234567890"

    @pytest.mark.unit
    def test_contact_requires_name(self):
        """Test that name is required."""
        with pytest.raises(ValidationError):
            Contact(email="test@example.com")

    @pytest.mark.unit
    def test_contact_email_validation(self):
        """Test email validation."""
        # Valid email
        contact = Contact(name="Test", email="valid@example.com")
        assert contact.email == "valid@example.com"

        # Invalid email should raise error
        with pytest.raises(ValidationError):
            Contact(name="Test", email="invalid-email")

    @pytest.mark.unit
    def test_contact_optional_fields(self):
        """Test contact with only required fields."""
        contact = Contact(name="Minimal Contact")
        assert contact.name == "Minimal Contact"
        assert contact.email is None
        assert contact.phone is None


class TestFileActivity:
    """Tests for FileActivity model."""

    @pytest.mark.unit
    def test_create_file_activity(self):
        """Test creating file activity record."""
        activity = FileActivity(
            filepath="data/file.txt",
            action="created"
        )
        assert activity.filepath == "data/file.txt"
        assert activity.action == "created"

    @pytest.mark.unit
    def test_file_activity_requires_path(self):
        """Test that filepath is required."""
        with pytest.raises(ValidationError):
            FileActivity(
                action="modified"
            )

    @pytest.mark.unit
    def test_file_activity_event_types(self):
        """Test different event types."""
        for action in ["created", "modified", "deleted", "moved"]:
            activity = FileActivity(
                filepath="data/test.txt",
                action=action
            )
            assert activity.action == action
