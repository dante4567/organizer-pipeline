"""
Task/Todo models with validation and security.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import Field, validator

from .base import BaseModel


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TodoItem(BaseModel):
    """
    Secure todo item model with comprehensive validation.
    """

    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Task status")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")
    tags: List[str] = Field(default_factory=list, max_items=10, description="Task tags")
    assigned_to: Optional[str] = Field(None, max_length=100, description="Assigned person")
    estimated_hours: Optional[float] = Field(None, ge=0, le=1000, description="Estimated effort in hours")

    @validator("tags")
    def validate_tags(cls, v):
        """Validate and sanitize tags."""
        import re
        tag_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        sanitized_tags = []
        for tag in v:
            clean_tag = tag.strip().lower()
            if not clean_tag:
                continue
            if len(clean_tag) > 30:
                raise ValueError(f"Tag too long: {clean_tag}")
            if not tag_pattern.match(clean_tag):
                raise ValueError(f"Invalid tag format: {clean_tag}")
            if clean_tag not in sanitized_tags:  # Remove duplicates
                sanitized_tags.append(clean_tag)
        return sanitized_tags

    @validator("title", "description")
    def sanitize_text(cls, v):
        """Sanitize text fields to prevent XSS."""
        if v is None:
            return v
        import html
        return html.escape(v.strip())

    @validator("completed_at")
    def validate_completion(cls, v, values):
        """Ensure completion timestamp is valid."""
        if v and "status" in values and values["status"] != TaskStatus.COMPLETED:
            raise ValueError("completed_at can only be set when status is completed")
        return v

    def mark_completed(self) -> None:
        """Mark task as completed with timestamp."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(datetime.now().astimezone().tzinfo)
        self.update_timestamp()

    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date or self.status == TaskStatus.COMPLETED:
            return False
        return self.due_date < datetime.now(self.due_date.tzinfo)

    def get_priority_score(self) -> int:
        """Get numeric priority score for sorting."""
        priority_scores = {
            TaskPriority.LOW: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.HIGH: 3,
            TaskPriority.URGENT: 4
        }
        return priority_scores.get(self.priority, 2)