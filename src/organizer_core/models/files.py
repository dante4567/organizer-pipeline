"""
File activity models with validation and security.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import Field, validator

from .base import BaseModel


class FileAction(str, Enum):
    """File action enumeration."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"
    ACCESSED = "accessed"


class FileType(str, Enum):
    """File type enumeration for categorization."""
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    ARCHIVE = "archive"
    CODE = "code"
    DATA = "data"
    OTHER = "other"


class FileActivity(BaseModel):
    """
    Secure file activity model with path validation.
    """

    filepath: str = Field(..., min_length=1, max_length=500, description="File path")
    action: FileAction = Field(..., description="File action performed")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    file_type: Optional[FileType] = Field(None, description="File type category")
    mime_type: Optional[str] = Field(None, max_length=100, description="MIME type")
    checksum: Optional[str] = Field(None, max_length=64, description="File checksum (SHA-256)")
    description: Optional[str] = Field(None, max_length=500, description="Activity description")

    @validator("filepath")
    def validate_filepath(cls, v):
        """Validate and sanitize file path."""
        import os
        # Normalize path and check for directory traversal
        normalized = os.path.normpath(v)

        # Prevent directory traversal attacks
        if ".." in normalized or normalized.startswith("/"):
            # Only allow relative paths within allowed directories
            if not any(normalized.startswith(allowed) for allowed in [
                "data/", "uploads/", "documents/", "temp/"
            ]):
                raise ValueError(f"Invalid file path: {v}")

        # Check path length and characters
        if len(normalized) > 500:
            raise ValueError("File path too long")

        # Only allow safe characters
        import re
        safe_pattern = re.compile(r'^[a-zA-Z0-9._/\-\s]+$')
        if not safe_pattern.match(normalized):
            raise ValueError(f"Invalid characters in file path: {v}")

        return normalized

    @validator("checksum")
    def validate_checksum(cls, v):
        """Validate checksum format."""
        if v is None:
            return v
        import re
        # SHA-256 checksum pattern
        sha256_pattern = re.compile(r'^[a-fA-F0-9]{64}$')
        if not sha256_pattern.match(v):
            raise ValueError("Invalid SHA-256 checksum format")
        return v.lower()

    @validator("mime_type")
    def validate_mime_type(cls, v):
        """Validate MIME type format."""
        if v is None:
            return v
        import re
        mime_pattern = re.compile(r'^[a-z]+/[a-z0-9][a-z0-9\-\+\.]*$')
        if not mime_pattern.match(v):
            raise ValueError(f"Invalid MIME type format: {v}")
        return v

    @classmethod
    def detect_file_type(cls, filepath: str, mime_type: Optional[str] = None) -> FileType:
        """Detect file type from extension or MIME type."""
        path = Path(filepath)
        extension = path.suffix.lower()

        # Document extensions
        if extension in ['.pdf', '.doc', '.docx', '.txt', '.md', '.rtf', '.odt']:
            return FileType.DOCUMENT

        # Image extensions
        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']:
            return FileType.IMAGE

        # Video extensions
        if extension in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']:
            return FileType.VIDEO

        # Audio extensions
        if extension in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']:
            return FileType.AUDIO

        # Archive extensions
        if extension in ['.zip', '.tar', '.gz', '.rar', '.7z', '.bz2']:
            return FileType.ARCHIVE

        # Code extensions
        if extension in ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.go', '.rs']:
            return FileType.CODE

        # Data extensions
        if extension in ['.json', '.xml', '.csv', '.yaml', '.yml', '.sql', '.db']:
            return FileType.DATA

        # Check MIME type if extension doesn't match
        if mime_type:
            if mime_type.startswith('image/'):
                return FileType.IMAGE
            elif mime_type.startswith('video/'):
                return FileType.VIDEO
            elif mime_type.startswith('audio/'):
                return FileType.AUDIO
            elif mime_type.startswith('text/'):
                return FileType.DOCUMENT

        return FileType.OTHER

    def get_relative_time(self) -> str:
        """Get human-readable relative time."""
        now = datetime.now(self.created_at.tzinfo)
        delta = now - self.created_at

        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"