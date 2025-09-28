"""
Database connection management for the organizer API.
"""

import logging
import aiosqlite
from pathlib import Path
from organizer_core.config import get_settings

logger = logging.getLogger(__name__)

# Global database connection
_db_connection = None


async def init_database() -> None:
    """Initialize database connection and create tables."""
    global _db_connection
    settings = get_settings()

    # Ensure data directory exists
    db_path = Path(settings.data_dir) / "organizer.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database
    _db_connection = await aiosqlite.connect(str(db_path))
    await _db_connection.execute("PRAGMA foreign_keys = ON")

    # Create tables
    await _create_tables()
    logger.info(f"Database initialized at {db_path}")


async def _create_tables() -> None:
    """Create database tables if they don't exist."""
    tables = [
        """
        CREATE TABLE IF NOT EXISTS calendar_events (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            location TEXT,
            event_type TEXT,
            attendees TEXT,  -- JSON array
            reminder_minutes INTEGER,
            recurrence_rule TEXT,
            calendar_name TEXT,
            all_day BOOLEAN DEFAULT FALSE,
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            due_date TEXT,
            completed_at TEXT,
            tags TEXT,  -- JSON array
            assigned_to TEXT,
            estimated_hours REAL,
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            company TEXT,
            birthday TEXT,
            notes TEXT,
            tags TEXT,  -- JSON array
            social_profiles TEXT,  -- JSON object
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS file_activities (
            id TEXT PRIMARY KEY,
            filepath TEXT NOT NULL,
            action TEXT NOT NULL,
            file_size INTEGER,
            file_type TEXT,
            mime_type TEXT,
            checksum TEXT,
            description TEXT,
            created_at TEXT
        )
        """
    ]

    for table_sql in tables:
        await _db_connection.execute(table_sql)

    await _db_connection.commit()


async def get_database() -> aiosqlite.Connection:
    """Get database connection."""
    global _db_connection
    if _db_connection is None:
        raise RuntimeError("Database not initialized")
    return _db_connection


async def close_database() -> None:
    """Close database connection."""
    global _db_connection
    if _db_connection:
        await _db_connection.close()
        _db_connection = None
        logger.info("Database connection closed")