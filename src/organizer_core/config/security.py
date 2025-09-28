"""
Security configuration and utilities.
"""

import secrets
import hashlib
from typing import List, Optional
from pydantic import BaseModel


class SecurityConfig:
    """Security configuration and utilities."""

    @staticmethod
    def generate_secret_key(length: int = 32) -> str:
        """Generate a secure random secret key."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_sensitive_data(data: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash sensitive data with salt."""
        if salt is None:
            salt = secrets.token_hex(16)

        # Use PBKDF2 for secure hashing
        import hashlib
        hash_obj = hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
        return hash_obj.hex(), salt

    @staticmethod
    def verify_hash(data: str, hashed: str, salt: str) -> bool:
        """Verify hashed data."""
        test_hash, _ = SecurityConfig.hash_sensitive_data(data, salt)
        return secrets.compare_digest(test_hash, hashed)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal."""
        import re
        import os

        # Remove path separators and dangerous characters
        clean_name = re.sub(r'[^\w\-_\.]', '_', filename)

        # Remove leading dots and ensure reasonable length
        clean_name = clean_name.lstrip('.')[:255]

        # Ensure we have something left
        if not clean_name:
            clean_name = "file"

        return clean_name

    @staticmethod
    def validate_cors_origins(origins: List[str]) -> List[str]:
        """Validate CORS origins for security."""
        import re

        valid_origins = []
        for origin in origins:
            # Allow localhost for development
            if origin.startswith(("http://localhost:", "https://localhost:")):
                valid_origins.append(origin)
                continue

            # Validate proper URL format
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?)'  # domain
                r'(?::\d+)?'  # optional port
                r'$', re.IGNORECASE)

            if url_pattern.match(origin):
                valid_origins.append(origin)

        return valid_origins

    @staticmethod
    def create_content_security_policy() -> str:
        """Create a secure Content Security Policy."""
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    whitelist_ips: List[str] = []

    def is_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted."""
        return ip in self.whitelist_ips or ip.startswith("127.0.0.1")