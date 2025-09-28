"""
Input validation classes for security and data integrity.
"""

import re
import html
from typing import Any, Dict, List, Optional
from datetime import datetime
from email_validator import validate_email, EmailNotValidError


class ValidationError(Exception):
    """Custom validation error with detailed information."""

    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        super().__init__(message)
        self.field = field
        self.value = value


class InputValidator:
    """Comprehensive input validator for all user inputs."""

    # Common regex patterns
    SAFE_TEXT_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,!?()@#+]+$')
    PHONE_PATTERN = re.compile(r'^[\+]?[\d\s\-\(\)]{7,20}$')
    TAG_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')

    @staticmethod
    def validate_text(text: str, field_name: str = "text",
                     min_length: int = 0, max_length: int = 1000,
                     allow_html: bool = False) -> str:
        """
        Validate and sanitize text input.

        Args:
            text: Input text to validate
            field_name: Name of the field being validated
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML tags

        Returns:
            Sanitized text

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(text, str):
            raise ValidationError(f"{field_name} must be a string", field_name, text)

        # Strip whitespace
        text = text.strip()

        # Check length
        if len(text) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters long",
                field_name, text
            )

        if len(text) > max_length:
            raise ValidationError(
                f"{field_name} must be no more than {max_length} characters long",
                field_name, text
            )

        # Sanitize HTML if not allowed
        if not allow_html:
            text = html.escape(text)

        # Check for dangerous patterns
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
            r'onload=',
            r'onerror=',
        ]

        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, text_lower):
                raise ValidationError(
                    f"{field_name} contains potentially dangerous content",
                    field_name, text
                )

        return text

    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate email address.

        Args:
            email: Email address to validate

        Returns:
            Normalized email address

        Raises:
            ValidationError: If email is invalid
        """
        if not email:
            raise ValidationError("Email cannot be empty", "email", email)

        try:
            # Use email-validator library for robust validation
            validated_email = validate_email(email)
            return validated_email.email
        except EmailNotValidError as e:
            raise ValidationError(f"Invalid email address: {str(e)}", "email", email)

    @staticmethod
    def validate_phone(phone: str) -> str:
        """
        Validate and normalize phone number.

        Args:
            phone: Phone number to validate

        Returns:
            Normalized phone number

        Raises:
            ValidationError: If phone number is invalid
        """
        if not phone:
            raise ValidationError("Phone number cannot be empty", "phone", phone)

        # Remove extra spaces and normalize
        phone = re.sub(r'\s+', ' ', phone.strip())

        # Validate format
        if not InputValidator.PHONE_PATTERN.match(phone):
            raise ValidationError(
                "Invalid phone number format. Use international format like +1234567890",
                "phone", phone
            )

        return phone

    @staticmethod
    def validate_datetime(dt_str: str, field_name: str = "datetime") -> datetime:
        """
        Validate and parse datetime string.

        Args:
            dt_str: Datetime string to validate
            field_name: Name of the field being validated

        Returns:
            Parsed datetime object

        Raises:
            ValidationError: If datetime is invalid
        """
        if not dt_str:
            raise ValidationError(f"{field_name} cannot be empty", field_name, dt_str)

        try:
            from dateutil import parser
            dt = parser.parse(dt_str)

            # Ensure timezone awareness
            if dt.tzinfo is None:
                # Assume UTC if no timezone specified
                from datetime import timezone
                dt = dt.replace(tzinfo=timezone.utc)

            return dt
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"Invalid {field_name} format: {str(e)}",
                field_name, dt_str
            )

    @staticmethod
    def validate_tags(tags: List[str]) -> List[str]:
        """
        Validate and sanitize list of tags.

        Args:
            tags: List of tags to validate

        Returns:
            Sanitized list of unique tags

        Raises:
            ValidationError: If any tag is invalid
        """
        if not isinstance(tags, list):
            raise ValidationError("Tags must be a list", "tags", tags)

        if len(tags) > 10:
            raise ValidationError("Maximum 10 tags allowed", "tags", tags)

        validated_tags = []
        for tag in tags:
            if not isinstance(tag, str):
                raise ValidationError("All tags must be strings", "tags", tag)

            tag = tag.strip().lower()
            if not tag:
                continue

            if len(tag) > 30:
                raise ValidationError("Tag too long (max 30 characters)", "tags", tag)

            if not InputValidator.TAG_PATTERN.match(tag):
                raise ValidationError(
                    "Tag contains invalid characters. Use only letters, numbers, hyphens, and underscores",
                    "tags", tag
                )

            if tag not in validated_tags:  # Remove duplicates
                validated_tags.append(tag)

        return validated_tags

    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate and sanitize filename.

        Args:
            filename: Filename to validate

        Returns:
            Sanitized filename

        Raises:
            ValidationError: If filename is invalid
        """
        if not filename:
            raise ValidationError("Filename cannot be empty", "filename", filename)

        # Remove path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.strip('. ')  # Remove leading/trailing dots and spaces

        if len(filename) > 255:
            raise ValidationError("Filename too long (max 255 characters)", "filename", filename)

        if not filename:
            raise ValidationError("Filename cannot be empty after sanitization", "filename", filename)

        # Check for reserved names on Windows
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }

        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in reserved_names:
            filename = f"file_{filename}"

        return filename

    @staticmethod
    def validate_priority(priority: str) -> str:
        """
        Validate task priority.

        Args:
            priority: Priority string to validate

        Returns:
            Validated priority

        Raises:
            ValidationError: If priority is invalid
        """
        valid_priorities = {'low', 'medium', 'high', 'urgent'}
        priority = priority.lower().strip()

        if priority not in valid_priorities:
            raise ValidationError(
                f"Invalid priority. Must be one of: {', '.join(valid_priorities)}",
                "priority", priority
            )

        return priority

    @staticmethod
    def validate_url(url: str, field_name: str = "url") -> str:
        """
        Validate URL format.

        Args:
            url: URL to validate
            field_name: Name of the field being validated

        Returns:
            Validated URL

        Raises:
            ValidationError: If URL is invalid
        """
        if not url:
            raise ValidationError(f"{field_name} cannot be empty", field_name, url)

        url = url.strip()

        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP address
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not url_pattern.match(url):
            raise ValidationError(f"Invalid {field_name} format", field_name, url)

        return url