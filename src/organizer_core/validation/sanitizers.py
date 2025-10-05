"""
Sanitization utilities for secure input handling.
"""

import re
import html
from pathlib import Path
from typing import Optional


class TextSanitizer:
    """Sanitize text inputs to prevent XSS and injection attacks."""

    @staticmethod
    def sanitize_html(text: str) -> str:
        """
        Escape HTML special characters to prevent XSS.

        Args:
            text: Text to sanitize

        Returns:
            HTML-escaped text
        """
        return html.escape(text)

    @staticmethod
    def remove_html_tags(text: str) -> str:
        """
        Remove all HTML tags from text.

        Args:
            text: Text with potential HTML tags

        Returns:
            Text with HTML tags removed
        """
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text)
        # Unescape HTML entities
        return html.unescape(clean)

    @staticmethod
    def sanitize_sql(text: str) -> str:
        """
        Basic SQL injection prevention (use parameterized queries instead).

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        # Remove common SQL injection patterns
        dangerous_patterns = [
            r"'--",
            r"';",
            r'" OR "1"="1',
            r"' OR '1'='1",
            r"DROP TABLE",
            r"DELETE FROM",
            r"INSERT INTO",
            r"UPDATE ",
            r"EXEC ",
            r"EXECUTE ",
        ]

        text_upper = text.upper()
        for pattern in dangerous_patterns:
            if pattern.upper() in text_upper:
                # Replace with safe placeholder
                text = re.sub(pattern, '[FILTERED]', text, flags=re.IGNORECASE)

        return text


class PathSanitizer:
    """Sanitize file paths to prevent directory traversal attacks."""

    @staticmethod
    def sanitize_path(path: str, base_dir: Optional[str] = None) -> Path:
        """
        Sanitize a file path to prevent directory traversal.

        Args:
            path: Path to sanitize
            base_dir: Base directory to restrict access to

        Returns:
            Sanitized Path object

        Raises:
            ValueError: If path attempts directory traversal
        """
        # Convert to Path object
        clean_path = Path(path).resolve()

        # Check for directory traversal
        if '..' in path or path.startswith('/'):
            raise ValueError("Path contains directory traversal or absolute path")

        # If base_dir specified, ensure path is within it
        if base_dir:
            base = Path(base_dir).resolve()
            try:
                # Check if path is relative to base_dir
                clean_path.relative_to(base)
            except ValueError:
                raise ValueError(f"Path must be within {base_dir}")

        return clean_path

    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """
        Check if filename is safe (no path traversal, special chars).

        Args:
            filename: Filename to check

        Returns:
            True if safe, False otherwise
        """
        # Check for path separators
        if '/' in filename or '\\' in filename:
            return False

        # Check for parent directory reference
        if '..' in filename:
            return False

        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
        if any(char in filename for char in dangerous_chars):
            return False

        return True

    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        Get a safe version of a filename by removing dangerous characters.

        Args:
            filename: Original filename

        Returns:
            Safe filename
        """
        # Remove path components
        filename = Path(filename).name

        # Remove/replace dangerous characters
        filename = re.sub(r'[<>:"/\\|?*\x00]', '_', filename)

        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')

        # Ensure not empty
        if not filename:
            filename = 'unnamed_file'

        return filename
