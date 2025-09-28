"""
Secure configuration settings using environment variables.
No secrets in files - everything from environment.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    provider: str = Field("demo", description="LLM provider: openai, anthropic, groq, ollama, demo")
    model: str = Field("demo", description="Model name")
    api_key: Optional[str] = Field(None, description="API key (from environment)")
    base_url: Optional[str] = Field(None, description="Custom API base URL")
    max_tokens: int = Field(2000, ge=100, le=8000, description="Maximum tokens per request")
    temperature: float = Field(0.3, ge=0.0, le=2.0, description="Response temperature")
    timeout: int = Field(30, ge=5, le=300, description="Request timeout in seconds")

    class Config:
        env_prefix = "LLM_"


class CalDAVSettings(BaseSettings):
    """CalDAV configuration."""

    url: Optional[str] = Field(None, description="CalDAV server URL")
    username: Optional[str] = Field(None, description="Username")
    password: Optional[str] = Field(None, description="Password (from environment)")
    calendar_name: str = Field("Personal", description="Default calendar name")
    sync_interval: int = Field(300, ge=60, description="Sync interval in seconds")

    class Config:
        env_prefix = "CALDAV_"

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        """Validate CalDAV URL format."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("CalDAV URL must start with http:// or https://")
        return v


class CardDAVSettings(BaseSettings):
    """CardDAV configuration."""

    url: Optional[str] = Field(None, description="CardDAV server URL")
    username: Optional[str] = Field(None, description="Username")
    password: Optional[str] = Field(None, description="Password (from environment)")
    addressbook_name: str = Field("Personal", description="Default addressbook name")
    sync_interval: int = Field(600, ge=60, description="Sync interval in seconds")

    class Config:
        env_prefix = "CARDDAV_"

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        """Validate CardDAV URL format."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("CardDAV URL must start with http:// or https://")
        return v


class MonitoringSettings(BaseSettings):
    """File monitoring configuration."""

    enabled: bool = Field(True, description="Enable file monitoring")
    watch_directories: List[str] = Field(
        default_factory=lambda: ["./data/uploads", "./data/documents"],
        description="Directories to monitor"
    )
    file_extensions: List[str] = Field(
        default_factory=lambda: [".txt", ".md", ".pdf", ".doc", ".docx"],
        description="File extensions to monitor"
    )
    daily_summary_time: str = Field("18:00", description="Daily summary time (HH:MM)")
    max_file_size_mb: int = Field(100, ge=1, le=1000, description="Maximum file size to process")

    class Config:
        env_prefix = "MONITORING_"

    @field_validator("watch_directories")
    @classmethod
    def validate_directories(cls, v):
        """Validate watch directories."""
        validated = []
        for directory in v:
            # Prevent directory traversal
            if ".." in directory or directory.startswith("/etc") or directory.startswith("/root"):
                continue
            validated.append(directory)
        return validated


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    url: str = Field("sqlite:///./data/organizer.db", description="Database URL")
    pool_size: int = Field(10, ge=1, le=100, description="Connection pool size")
    echo: bool = Field(False, description="Enable SQL logging")

    class Config:
        env_prefix = "DATABASE_"


class SecuritySettings(BaseSettings):
    """Security configuration."""

    secret_key: str = Field(..., min_length=32, description="Secret key for sessions")
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins"
    )
    rate_limit_per_minute: int = Field(60, ge=1, le=1000, description="Rate limit per minute")
    max_request_size_mb: int = Field(10, ge=1, le=100, description="Maximum request size")

    class Config:
        env_prefix = "SECURITY_"


class Settings(BaseSettings):
    """Main application settings."""

    app_name: str = Field("Organizer Pipeline", description="Application name")
    version: str = Field("2.0.0", description="Application version")
    debug: bool = Field(False, description="Debug mode")
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8080, ge=1, le=65535, description="Server port")
    data_dir: str = Field("./data", description="Data directory")
    log_level: str = Field("INFO", description="Logging level")

    # Nested settings
    llm: LLMSettings = Field(default_factory=LLMSettings)
    caldav: CalDAVSettings = Field(default_factory=CalDAVSettings)
    carddav: CardDAVSettings = Field(default_factory=CardDAVSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @field_validator("data_dir")
    @classmethod
    def validate_data_dir(cls, v):
        """Validate data directory path."""
        import os
        # Ensure data directory is safe
        if ".." in v or v.startswith("/etc") or v.startswith("/root"):
            raise ValueError("Invalid data directory path")

        # Create directory if it doesn't exist
        os.makedirs(v, exist_ok=True)
        return v

    def get_database_url(self) -> str:
        """Get the full database URL."""
        if self.database.url.startswith("sqlite"):
            # Ensure SQLite database is in data directory
            if ":///" in self.database.url:
                db_path = self.database.url.split(":///")[1]
                if not db_path.startswith("./data/"):
                    return f"sqlite:///{self.data_dir}/organizer.db"
        return self.database.url


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()