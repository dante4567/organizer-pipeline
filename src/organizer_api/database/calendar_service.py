"""
Calendar events CRUD service for database operations.
"""

import json
import logging
from typing import List, Optional
from datetime import datetime, timezone
import uuid

import aiosqlite
from organizer_core.models.calendar import CalendarEvent, EventType

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for calendar event database operations."""

    @staticmethod
    async def create_event(db: aiosqlite.Connection, event: CalendarEvent) -> CalendarEvent:
        """
        Create a new calendar event in the database.

        Args:
            db: Database connection
            event: Event to create

        Returns:
            Created event with ID and timestamps
        """
        # Generate ID if not provided
        if not event.id:
            event.id = str(uuid.uuid4())

        # Set timestamps
        now = datetime.now(timezone.utc)
        event.created_at = now
        event.updated_at = now

        # Serialize attendees to JSON
        attendees_json = json.dumps(event.attendees) if event.attendees else None

        # Convert datetime to ISO format string
        start_time_str = event.start_time.isoformat() if event.start_time else None
        end_time_str = event.end_time.isoformat() if event.end_time else None

        query = """
            INSERT INTO calendar_events (
                id, title, description, start_time, end_time, location,
                event_type, attendees, reminder_minutes, recurrence_rule,
                calendar_name, all_day, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        await db.execute(
            query,
            (
                event.id,
                event.title,
                event.description,
                start_time_str,
                end_time_str,
                event.location,
                event.event_type,
                attendees_json,
                event.reminder_minutes,
                event.recurrence_rule,
                event.calendar_name,
                event.all_day,
                event.created_at.isoformat(),
                event.updated_at.isoformat()
            )
        )
        await db.commit()

        logger.info(f"Created event: {event.id} - {event.title}")
        return event

    @staticmethod
    async def get_event(db: aiosqlite.Connection, event_id: str) -> Optional[CalendarEvent]:
        """
        Get a single event by ID.

        Args:
            db: Database connection
            event_id: Event ID

        Returns:
            Event if found, None otherwise
        """
        query = "SELECT * FROM calendar_events WHERE id = ?"

        async with db.execute(query, (event_id,)) as cursor:
            row = await cursor.fetchone()

        if not row:
            return None

        return CalendarService._row_to_event(row)

    @staticmethod
    async def get_events(
        db: aiosqlite.Connection,
        event_type: Optional[EventType] = None,
        calendar_name: Optional[str] = None,
        start_after: Optional[datetime] = None,
        start_before: Optional[datetime] = None,
        limit: int = 100
    ) -> List[CalendarEvent]:
        """
        Get events with optional filtering.

        Args:
            db: Database connection
            event_type: Filter by event type
            calendar_name: Filter by calendar name
            start_after: Filter events starting after this time
            start_before: Filter events starting before this time
            limit: Maximum number of events to return

        Returns:
            List of events
        """
        query = "SELECT * FROM calendar_events WHERE 1=1"
        params = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        if calendar_name:
            query += " AND calendar_name = ?"
            params.append(calendar_name)

        if start_after:
            query += " AND start_time > ?"
            params.append(start_after.isoformat())

        if start_before:
            query += " AND start_time < ?"
            params.append(start_before.isoformat())

        query += " ORDER BY start_time ASC LIMIT ?"
        params.append(limit)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

        events = [CalendarService._row_to_event(row) for row in rows]
        logger.info(f"Retrieved {len(events)} events")
        return events

    @staticmethod
    async def update_event(
        db: aiosqlite.Connection,
        event_id: str,
        event: CalendarEvent
    ) -> Optional[CalendarEvent]:
        """
        Update an existing event.

        Args:
            db: Database connection
            event_id: Event ID to update
            event: Updated event data

        Returns:
            Updated event if found, None otherwise
        """
        # Check if event exists
        existing = await CalendarService.get_event(db, event_id)
        if not existing:
            return None

        # Update timestamp
        event.updated_at = datetime.now(timezone.utc)
        event.id = event_id  # Ensure ID doesn't change

        # Serialize attendees
        attendees_json = json.dumps(event.attendees) if event.attendees else None

        # Convert datetime to ISO format
        start_time_str = event.start_time.isoformat() if event.start_time else None
        end_time_str = event.end_time.isoformat() if event.end_time else None

        query = """
            UPDATE calendar_events SET
                title = ?,
                description = ?,
                start_time = ?,
                end_time = ?,
                location = ?,
                event_type = ?,
                attendees = ?,
                reminder_minutes = ?,
                recurrence_rule = ?,
                calendar_name = ?,
                all_day = ?,
                updated_at = ?
            WHERE id = ?
        """

        await db.execute(
            query,
            (
                event.title,
                event.description,
                start_time_str,
                end_time_str,
                event.location,
                event.event_type,
                attendees_json,
                event.reminder_minutes,
                event.recurrence_rule,
                event.calendar_name,
                event.all_day,
                event.updated_at.isoformat(),
                event_id
            )
        )
        await db.commit()

        logger.info(f"Updated event: {event_id}")
        return event

    @staticmethod
    async def delete_event(db: aiosqlite.Connection, event_id: str) -> bool:
        """
        Delete an event.

        Args:
            db: Database connection
            event_id: Event ID to delete

        Returns:
            True if deleted, False if not found
        """
        # Check if event exists
        existing = await CalendarService.get_event(db, event_id)
        if not existing:
            return False

        query = "DELETE FROM calendar_events WHERE id = ?"
        await db.execute(query, (event_id,))
        await db.commit()

        logger.info(f"Deleted event: {event_id}")
        return True

    @staticmethod
    def _row_to_event(row: tuple) -> CalendarEvent:
        """
        Convert database row to CalendarEvent.

        Args:
            row: Database row tuple

        Returns:
            CalendarEvent instance
        """
        # Parse JSON fields
        attendees = json.loads(row[7]) if row[7] else []

        # Parse datetime fields
        from dateutil import parser

        start_time = parser.parse(row[3]) if row[3] else None
        end_time = parser.parse(row[4]) if row[4] else None
        created_at = parser.parse(row[12]) if row[12] else datetime.now(timezone.utc)
        updated_at = parser.parse(row[13]) if row[13] else datetime.now(timezone.utc)

        return CalendarEvent(
            id=row[0],
            title=row[1],
            description=row[2],
            start_time=start_time,
            end_time=end_time,
            location=row[5],
            event_type=row[6],
            attendees=attendees,
            reminder_minutes=row[8],
            recurrence_rule=row[9],
            calendar_name=row[10],
            all_day=bool(row[11]),
            created_at=created_at,
            updated_at=updated_at
        )
