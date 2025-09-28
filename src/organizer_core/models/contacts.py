"""
Contact models with validation and security.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import Field, validator, EmailStr

from .base import BaseModel


class Contact(BaseModel):
    """
    Secure contact model with comprehensive validation.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Contact name")
    email: Optional[EmailStr] = Field(None, description="Contact email address")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    address: Optional[str] = Field(None, max_length=300, description="Contact address")
    company: Optional[str] = Field(None, max_length=100, description="Company name")
    birthday: Optional[datetime] = Field(None, description="Contact birthday")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    tags: List[str] = Field(default_factory=list, max_items=10, description="Contact tags")
    social_profiles: dict = Field(default_factory=dict, description="Social media profiles")

    @validator("phone")
    def validate_phone(cls, v):
        """Validate and sanitize phone number."""
        if v is None:
            return v
        import re
        # Remove all non-digit characters except + and spaces
        phone_clean = re.sub(r'[^\d\+\s\-\(\)]', '', v.strip())
        # Basic phone validation (international format)
        phone_pattern = re.compile(r'^[\+]?[\d\s\-\(\)]{7,20}$')
        if not phone_pattern.match(phone_clean):
            raise ValueError(f"Invalid phone number format: {v}")
        return phone_clean

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

    @validator("name", "company", "notes")
    def sanitize_text(cls, v):
        """Sanitize text fields to prevent XSS."""
        if v is None:
            return v
        import html
        return html.escape(v.strip())

    @validator("social_profiles")
    def validate_social_profiles(cls, v):
        """Validate social media profiles."""
        if not isinstance(v, dict):
            return {}

        allowed_platforms = {
            'twitter', 'linkedin', 'github', 'facebook',
            'instagram', 'youtube', 'website'
        }

        validated_profiles = {}
        for platform, url in v.items():
            if platform.lower() in allowed_platforms and isinstance(url, str):
                # Basic URL validation
                import re
                url_pattern = re.compile(
                    r'^https?://'  # http:// or https://
                    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                    r'localhost|'  # localhost...
                    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                    r'(?::\d+)?'  # optional port
                    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

                if url_pattern.match(url.strip()):
                    validated_profiles[platform.lower()] = url.strip()

        return validated_profiles

    def get_display_name(self) -> str:
        """Get formatted display name."""
        return self.name

    def has_birthday_this_month(self) -> bool:
        """Check if contact has birthday this month."""
        if not self.birthday:
            return False
        today = datetime.now()
        return self.birthday.month == today.month

    def model_dump_safe(self) -> dict:
        """Override to exclude sensitive contact information in some contexts."""
        data = super().model_dump_safe()
        # Could exclude certain fields based on privacy settings
        return data