"""
Calendar API router with full CRUD operations.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime
import aiosqlite

from organizer_core.models.calendar import CalendarEvent, EventType
from ..database.connection import get_database
from ..database.calendar_service import CalendarService

router = APIRouter()


@router.get("/events", response_model=List[CalendarEvent])
async def get_events(
    start_after: Optional[datetime] = Query(None, description="Filter events starting after this time"),
    start_before: Optional[datetime] = Query(None, description="Filter events starting before this time"),
    event_type: Optional[EventType] = Query(None, description="Filter by event type"),
    calendar_name: Optional[str] = Query(None, description="Filter by calendar name"),
    db: aiosqlite.Connection = Depends(get_database)
) -> List[CalendarEvent]:
    """Get calendar events with optional filtering."""
    events = await CalendarService.get_events(
        db,
        event_type=event_type,
        calendar_name=calendar_name,
        start_after=start_after,
        start_before=start_before
    )
    return events


@router.get("/events/{event_id}", response_model=CalendarEvent)
async def get_event(
    event_id: str,
    db: aiosqlite.Connection = Depends(get_database)
) -> CalendarEvent:
    """Get a single calendar event by ID."""
    event = await CalendarService.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return event


@router.post("/events", response_model=CalendarEvent, status_code=201)
async def create_event(
    event: CalendarEvent,
    db: aiosqlite.Connection = Depends(get_database)
) -> CalendarEvent:
    """Create a new calendar event."""
    created_event = await CalendarService.create_event(db, event)
    return created_event


@router.put("/events/{event_id}", response_model=CalendarEvent)
async def update_event(
    event_id: str,
    event: CalendarEvent,
    db: aiosqlite.Connection = Depends(get_database)
) -> CalendarEvent:
    """Update an existing calendar event."""
    updated_event = await CalendarService.update_event(db, event_id, event)
    if not updated_event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return updated_event


@router.delete("/events/{event_id}", status_code=204)
async def delete_event(
    event_id: str,
    db: aiosqlite.Connection = Depends(get_database)
) -> None:
    """Delete a calendar event."""
    deleted = await CalendarService.delete_event(db, event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
