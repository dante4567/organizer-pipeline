"""
Security and validation tests.
"""

import pytest
from datetime import datetime, timezone

from organizer_core.validation import (
    InputValidator,
    ValidationError,
    TextSanitizer,
    PathSanitizer
)


class TestInputValidator:
    """Tests for InputValidator."""

    @pytest.mark.security
    def test_validate_text_basic(self):
        """Test basic text validation."""
        result = InputValidator.validate_text("Hello world")
        assert result == "Hello world"

    @pytest.mark.security
    def test_validate_text_xss_protection(self):
        """Test XSS protection in text validation."""
        dangerous_input = "<script>alert('xss')</script>"
        result = InputValidator.validate_text(dangerous_input)
        # Should be escaped
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    @pytest.mark.security
    def test_validate_text_javascript_protocol(self):
        """Test blocking javascript: protocol."""
        with pytest.raises(ValidationError):
            InputValidator.validate_text("javascript:alert('xss')")

    @pytest.mark.security
    def test_validate_text_length_limits(self):
        """Test text length validation."""
        # Too short
        with pytest.raises(ValidationError):
            InputValidator.validate_text("", min_length=5)

        # Too long
        with pytest.raises(ValidationError):
            InputValidator.validate_text("x" * 1001, max_length=1000)

        # Just right
        result = InputValidator.validate_text("x" * 50, min_length=10, max_length=100)
        assert len(result) == 50

    @pytest.mark.security
    def test_validate_text_strips_whitespace(self):
        """Test that text is stripped of leading/trailing whitespace."""
        result = InputValidator.validate_text("  hello world  ")
        assert result == "hello world"

    @pytest.mark.unit
    def test_validate_email_valid(self):
        """Test validating valid email addresses."""
        valid_emails = [
            "user@example.com",
            "test.user@example.co.uk",
            "user+tag@example.com"
        ]
        for email in valid_emails:
            result = InputValidator.validate_email(email)
            assert "@" in result

    @pytest.mark.unit
    def test_validate_email_invalid(self):
        """Test rejecting invalid email addresses."""
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user @example.com",
            ""
        ]
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                InputValidator.validate_email(email)

    @pytest.mark.unit
    def test_validate_phone(self):
        """Test phone number validation."""
        valid_phones = [
            "+1234567890",
            "+1 234 567 890",
            "1234567890"
        ]
        for phone in valid_phones:
            result = InputValidator.validate_phone(phone)
            assert len(result) >= 7

    @pytest.mark.unit
    def test_validate_phone_invalid(self):
        """Test invalid phone numbers."""
        with pytest.raises(ValidationError):
            InputValidator.validate_phone("123")  # Too short

        with pytest.raises(ValidationError):
            InputValidator.validate_phone("")  # Empty

    @pytest.mark.unit
    def test_validate_datetime(self):
        """Test datetime validation."""
        valid_datetimes = [
            "2025-10-05T12:00:00Z",
            "2025-10-05 12:00:00",
            "October 5, 2025 12:00 PM"
        ]
        for dt_str in valid_datetimes:
            result = InputValidator.validate_datetime(dt_str)
            assert isinstance(result, datetime)
            assert result.tzinfo is not None  # Should be timezone-aware

    @pytest.mark.unit
    def test_validate_datetime_invalid(self):
        """Test invalid datetime strings."""
        with pytest.raises(ValidationError):
            InputValidator.validate_datetime("not-a-date")

        with pytest.raises(ValidationError):
            InputValidator.validate_datetime("")

    @pytest.mark.unit
    def test_validate_tags(self):
        """Test tag validation."""
        tags = ["work", "urgent", "project-x"]
        result = InputValidator.validate_tags(tags)
        assert len(result) == 3
        assert "work" in result

    @pytest.mark.unit
    def test_validate_tags_removes_duplicates(self):
        """Test that duplicate tags are removed."""
        tags = ["work", "work", "urgent"]
        result = InputValidator.validate_tags(tags)
        assert len(result) == 2
        assert result.count("work") == 1

    @pytest.mark.unit
    def test_validate_tags_max_limit(self):
        """Test maximum tag limit."""
        tags = [f"tag{i}" for i in range(15)]
        with pytest.raises(ValidationError):
            InputValidator.validate_tags(tags)

    @pytest.mark.security
    def test_validate_tags_invalid_characters(self):
        """Test rejecting tags with invalid characters."""
        with pytest.raises(ValidationError):
            InputValidator.validate_tags(["valid", "<script>"])

    @pytest.mark.unit
    def test_validate_filename(self):
        """Test filename validation."""
        result = InputValidator.validate_filename("document.txt")
        assert result == "document.txt"

    @pytest.mark.security
    def test_validate_filename_sanitization(self):
        """Test filename sanitization."""
        dangerous_names = [
            "../../../etc/passwd",
            "file<script>.txt",
            'file"name.txt',
            "file|name.txt"
        ]
        for name in dangerous_names:
            result = InputValidator.validate_filename(name)
            # Should not contain dangerous characters
            assert ".." not in result
            assert "<" not in result
            assert '"' not in result
            assert "|" not in result

    @pytest.mark.unit
    def test_validate_filename_reserved_windows_names(self):
        """Test handling of reserved Windows filenames."""
        reserved = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]
        for name in reserved:
            result = InputValidator.validate_filename(name)
            # Should be prefixed to avoid conflict
            assert result.startswith("file_")

    @pytest.mark.unit
    def test_validate_priority(self):
        """Test priority validation."""
        for priority in ["low", "medium", "high", "urgent"]:
            result = InputValidator.validate_priority(priority)
            assert result == priority

    @pytest.mark.unit
    def test_validate_priority_invalid(self):
        """Test invalid priority values."""
        with pytest.raises(ValidationError):
            InputValidator.validate_priority("extreme")

    @pytest.mark.unit
    def test_validate_url(self):
        """Test URL validation."""
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "https://example.com/path",
            "http://localhost:8080"
        ]
        for url in valid_urls:
            result = InputValidator.validate_url(url)
            assert result.startswith("http")

    @pytest.mark.unit
    def test_validate_url_invalid(self):
        """Test invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Only http/https allowed
            "",
            "javascript:alert(1)"
        ]
        for url in invalid_urls:
            with pytest.raises(ValidationError):
                InputValidator.validate_url(url)


class TestTextSanitizer:
    """Tests for TextSanitizer."""

    @pytest.mark.security
    def test_sanitize_html(self):
        """Test HTML sanitization."""
        html = "<p>Hello</p>"
        result = TextSanitizer.sanitize_html(html)
        assert "<p>" not in result
        assert "&lt;p&gt;" in result

    @pytest.mark.security
    def test_remove_html_tags(self):
        """Test HTML tag removal."""
        html = "<p>Hello <strong>world</strong></p>"
        result = TextSanitizer.remove_html_tags(html)
        assert result == "Hello world"
        assert "<" not in result

    @pytest.mark.security
    def test_sanitize_sql(self):
        """Test SQL injection prevention."""
        dangerous_sql = "'; DROP TABLE users; --"
        result = TextSanitizer.sanitize_sql(dangerous_sql)
        assert "DROP TABLE" not in result or "[FILTERED]" in result


class TestPathSanitizer:
    """Tests for PathSanitizer."""

    @pytest.mark.security
    def test_sanitize_path_blocks_traversal(self):
        """Test blocking directory traversal."""
        with pytest.raises(ValueError):
            PathSanitizer.sanitize_path("../../../etc/passwd")

    @pytest.mark.security
    def test_sanitize_path_blocks_absolute(self):
        """Test blocking absolute paths."""
        with pytest.raises(ValueError):
            PathSanitizer.sanitize_path("/etc/passwd")

    @pytest.mark.unit
    def test_is_safe_filename(self):
        """Test safe filename checking."""
        assert PathSanitizer.is_safe_filename("document.txt") is True
        assert PathSanitizer.is_safe_filename("../file.txt") is False
        assert PathSanitizer.is_safe_filename("/etc/passwd") is False
        assert PathSanitizer.is_safe_filename("file<script>.txt") is False

    @pytest.mark.unit
    def test_get_safe_filename(self):
        """Test getting safe filename."""
        result = PathSanitizer.get_safe_filename("../dangerous.txt")
        assert ".." not in result
        assert "/" not in result

        result = PathSanitizer.get_safe_filename("file<script>.txt")
        assert "<" not in result
        assert ">" not in result
