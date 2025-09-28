"""
Calendar event models with validation and security.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import Field, validator

from .base import BaseModel


class EventType(str, Enum):
    """Event type enumeration for categorization."""
    MEETING = "meeting"
    TASK = "task"
    REMINDER = "reminder"
    PERSONAL = "personal"
    WORK = "work"
    APPOINTMENT = "appointment"


class CalendarEvent(BaseModel):
    """
    Secure calendar event model with comprehensive validation.
    """

    title: str = Field(..., min_length=1, max_length=200, description="Event title")
    description: Optional[str] = Field(None, max_length=1000, description="Event description")
    start_time: datetime = Field(..., description="Event start time (timezone-aware)")
    end_time: Optional[datetime] = Field(None, description="Event end time (timezone-aware)")
    location: Optional[str] = Field(None, max_length=500, description="Event location")
    event_type: EventType = Field(EventType.PERSONAL, description="Event category")
    attendees: List[str] = Field(default_factory=list, max_items=50, description="List of attendee emails")
    reminder_minutes: Optional[int] = Field(15, ge=0, le=10080, description="Reminder time in minutes")
    recurrence_rule: Optional[str] = Field(None, max_length=200, description="RFC 5545 recurrence rule")
    calendar_name: Optional[str] = Field("Personal", max_length=100, description="Calendar name")
    all_day: bool = Field(False, description="All-day event flag")

    @validator("end_time")
    def validate_end_time(cls, v, values):
        """Ensure end time is after start time."""
        if v and "start_time" in values and v <= values["start_time"]:
            raise ValueError("End time must be after start time")
        return v

    @validator("attendees")
    def validate_attendees(cls, v):
        """Validate attendee email formats."""
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        for email in v:
            if not email_pattern.match(email):
                raise ValueError(f"Invalid email format: {email}")
        return v

    @validator("title")
    def sanitize_title(cls, v):
        """Sanitize title to prevent XSS."""
        import html
        return html.escape(v.strip())

    def get_duration_minutes(self) -> int:
        """Calculate event duration in minutes."""
        if not self.end_time:
            return 60  # Default 1 hour
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    def is_upcoming(self) -> bool:
        """Check if event is in the future."""
        return self.start_time > datetime.now(self.start_time.tzinfo)