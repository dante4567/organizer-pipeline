"""
Base model with security and validation features.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel as PydanticBaseModel, Field
import uuid


class BaseModel(PydanticBaseModel):
    """
    Secure base model with automatic ID generation, timestamps, and validation.
    """

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        """Pydantic configuration for security and performance."""
        # Security: Don't allow extra fields to prevent injection
        extra = "forbid"
        # Performance: Use enum values directly
        use_enum_values = True
        # Security: Validate all fields on assignment
        validate_assignment = True
        # Timezone aware datetimes
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def model_dump_safe(self) -> dict:
        """
        Safely dump model to dict, excluding sensitive fields if any.
        Override in subclasses to exclude sensitive data.
        """
        return self.model_dump(exclude_none=True)