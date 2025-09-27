#!/usr/bin/env python3
"""
Personal Data Management Service
A standalone FastAPI service for calendar, tasks, contacts, and file management
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from enum import Enum
import sqlite3
import json
import logging
import os
import asyncio
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import mimetypes
import re
from dateutil import parser as date_parser
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = os.getenv("DB_PATH", "/data/personal.db")
FILES_ROOT = os.getenv("FILES_ROOT", "/data/files")
DEFAULT_LLM = os.getenv("DEFAULT_LLM", "anthropic")
REMINDER_CHECK_MINUTES = int(os.getenv("REMINDER_CHECK_MINUTES", "5"))
DAILY_REVIEW_HOUR = int(os.getenv("DAILY_REVIEW_HOUR", "8"))
TIMEZONE = os.getenv("TIMEZONE", "UTC")

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Enums
class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"

class EventType(str, Enum):
    meeting = "meeting"
    task = "task"
    reminder = "reminder"
    personal = "personal"
    work = "work"

# Pydantic Models
class CalendarEvent(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    event_type: EventType = EventType.personal
    attendees: Optional[List[str]] = []
    reminder_minutes: Optional[int] = 15
    recurrence: Optional[str] = None  # RRULE format
    created_at: Optional[datetime] = None

class Task(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.pending
    priority: TaskPriority = TaskPriority.medium
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tags: Optional[List[str]] = []
    assigned_to: Optional[str] = None
    created_at: Optional[datetime] = None

class Contact(BaseModel):
    id: Optional[int] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    company: Optional[str] = None
    birthday: Optional[str] = None  # ISO date string
    notes: Optional[str] = None
    tags: Optional[List[str]] = []
    created_at: Optional[datetime] = None

class FileInfo(BaseModel):
    name: str
    path: str
    size: int
    modified_time: datetime
    mime_type: str
    is_directory: bool

class NaturalLanguageRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = {}

class NaturalLanguageResponse(BaseModel):
    type: str
    action: str
    data: Dict[str, Any]
    confidence: float
    response: str

# Database Management
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        try:
            # Calendar Events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    location TEXT,
                    event_type TEXT DEFAULT 'personal',
                    attendees TEXT DEFAULT '[]',
                    reminder_minutes INTEGER DEFAULT 15,
                    recurrence TEXT,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tasks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    priority TEXT DEFAULT 'medium',
                    due_date TIMESTAMP,
                    completed_at TIMESTAMP,
                    tags TEXT DEFAULT '[]',
                    assigned_to TEXT,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Contacts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    address TEXT,
                    company TEXT,
                    birthday TEXT,
                    notes TEXT,
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Reminders table for tracking notifications
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    task_id INTEGER,
                    reminder_time TIMESTAMP NOT NULL,
                    message TEXT NOT NULL,
                    sent BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
        finally:
            conn.close()

# LLM Integration
class LLMService:
    def __init__(self):
        self.provider = DEFAULT_LLM
        self.api_key = ANTHROPIC_API_KEY if self.provider == "anthropic" else OPENAI_API_KEY

    async def parse_natural_language(self, text: str, context: Dict = None) -> Dict[str, Any]:
        """Parse natural language text into structured commands"""
        if not self.api_key:
            return self._fallback_parse(text)

        try:
            if self.provider == "anthropic":
                return await self._parse_with_claude(text, context)
            elif self.provider == "openai":
                return await self._parse_with_openai(text, context)
            else:
                return self._fallback_parse(text)
        except Exception as e:
            logger.error(f"LLM parsing error: {e}")
            return self._fallback_parse(text)

    async def _parse_with_claude(self, text: str, context: Dict = None) -> Dict[str, Any]:
        """Parse using Claude API"""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        prompt = f"""Parse this natural language request into a structured command:

Text: "{text}"
Context: {json.dumps(context or {})}

Identify:
1. Type: calendar_event, task, contact, file, or query
2. Action: create, update, delete, get, list
3. Extract relevant fields based on type

For calendar_event: title, start_time, end_time, location, event_type, attendees
For task: title, description, priority, due_date, tags, assigned_to
For contact: name, email, phone, company, address
For query: what information is being requested

Return ONLY a JSON object with this structure:
{{
    "type": "calendar_event|task|contact|file|query",
    "action": "create|update|delete|get|list",
    "data": {{ extracted fields }},
    "confidence": 0.8,
    "response": "Natural language response about what will be done"
}}

Rules:
- Always return valid JSON
- Use ISO format for dates (YYYY-MM-DDTHH:MM:SS)
- Infer reasonable defaults for missing information
- Be confident in your parsing"""

        data = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            content = response.json()["content"][0]["text"]
            # Clean up JSON response
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            return json.loads(content.strip())
        else:
            raise Exception(f"Claude API error: {response.status_code}")

    async def _parse_with_openai(self, text: str, context: Dict = None) -> Dict[str, Any]:
        """Parse using OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        prompt = f"""Parse this natural language request: "{text}"

Return JSON with: type, action, data, confidence, response"""

        data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.3
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content.strip())
        else:
            raise Exception(f"OpenAI API error: {response.status_code}")

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback parsing without LLM"""
        text_lower = text.lower()

        # Simple pattern matching
        if any(word in text_lower for word in ["meeting", "appointment", "schedule", "calendar"]):
            # Try to extract time and title
            tomorrow = datetime.now() + timedelta(days=1)

            return {
                "type": "calendar_event",
                "action": "create",
                "data": {
                    "title": "Meeting",
                    "start_time": tomorrow.replace(hour=14, minute=0).isoformat(),
                    "event_type": "meeting"
                },
                "confidence": 0.6,
                "response": "I'll create a calendar event (using fallback parsing)"
            }

        elif any(word in text_lower for word in ["task", "todo", "remind", "do"]):
            return {
                "type": "task",
                "action": "create",
                "data": {
                    "title": text[:50],
                    "priority": "medium"
                },
                "confidence": 0.6,
                "response": "I'll create a task (using fallback parsing)"
            }

        elif any(word in text_lower for word in ["contact", "person", "add"]):
            return {
                "type": "contact",
                "action": "create",
                "data": {
                    "name": "New Contact"
                },
                "confidence": 0.5,
                "response": "I'll create a contact (using fallback parsing)"
            }

        else:
            return {
                "type": "query",
                "action": "get",
                "data": {"query": text},
                "confidence": 0.3,
                "response": "I'm not sure what you want to do. Try being more specific."
            }

# Services
class CalendarService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_event(self, event: CalendarEvent) -> int:
        conn = self.db.get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO calendar_events
                (title, description, start_time, end_time, location, event_type,
                 attendees, reminder_minutes, recurrence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.title, event.description, event.start_time.isoformat(),
                event.end_time.isoformat() if event.end_time else None,
                event.location, event.event_type.value,
                json.dumps(event.attendees or []),
                event.reminder_minutes, event.recurrence
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_events(self, start_time: datetime = None, end_time: datetime = None) -> List[CalendarEvent]:
        conn = self.db.get_connection()
        try:
            query = "SELECT * FROM calendar_events WHERE 1=1"
            params = []

            if start_time:
                query += " AND start_time >= ?"
                params.append(start_time.isoformat())

            if end_time:
                query += " AND start_time <= ?"
                params.append(end_time.isoformat())

            query += " ORDER BY start_time"

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_event(row) for row in rows]
        finally:
            conn.close()

    def get_today_events(self) -> List[CalendarEvent]:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return self.get_events(today, tomorrow)

    def get_event(self, event_id: int) -> Optional[CalendarEvent]:
        conn = self.db.get_connection()
        try:
            row = conn.execute("SELECT * FROM calendar_events WHERE id = ?", (event_id,)).fetchone()
            return self._row_to_event(row) if row else None
        finally:
            conn.close()

    def update_event(self, event_id: int, event: CalendarEvent) -> bool:
        conn = self.db.get_connection()
        try:
            conn.execute("""
                UPDATE calendar_events SET
                title = ?, description = ?, start_time = ?, end_time = ?,
                location = ?, event_type = ?, attendees = ?, reminder_minutes = ?, recurrence = ?
                WHERE id = ?
            """, (
                event.title, event.description, event.start_time.isoformat(),
                event.end_time.isoformat() if event.end_time else None,
                event.location, event.event_type.value,
                json.dumps(event.attendees or []),
                event.reminder_minutes, event.recurrence, event_id
            ))
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def delete_event(self, event_id: int) -> bool:
        conn = self.db.get_connection()
        try:
            conn.execute("DELETE FROM calendar_events WHERE id = ?", (event_id,))
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def _row_to_event(self, row) -> CalendarEvent:
        return CalendarEvent(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            start_time=datetime.fromisoformat(row["start_time"]),
            end_time=datetime.fromisoformat(row["end_time"]) if row["end_time"] else None,
            location=row["location"],
            event_type=EventType(row["event_type"]),
            attendees=json.loads(row["attendees"]),
            reminder_minutes=row["reminder_minutes"],
            recurrence=row["recurrence"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        )

class TaskService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_task(self, task: Task) -> int:
        conn = self.db.get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO tasks
                (title, description, status, priority, due_date, tags, assigned_to)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                task.title, task.description, task.status.value, task.priority.value,
                task.due_date.isoformat() if task.due_date else None,
                json.dumps(task.tags or []), task.assigned_to
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_tasks(self, status: TaskStatus = None, limit: int = 100) -> List[Task]:
        conn = self.db.get_connection()
        try:
            query = "SELECT * FROM tasks WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status.value)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_task(row) for row in rows]
        finally:
            conn.close()

    def get_task(self, task_id: int) -> Optional[Task]:
        conn = self.db.get_connection()
        try:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            return self._row_to_task(row) if row else None
        finally:
            conn.close()

    def update_task(self, task_id: int, task: Task) -> bool:
        conn = self.db.get_connection()
        try:
            completed_at = None
            if task.status == TaskStatus.completed and task.completed_at is None:
                completed_at = datetime.now().isoformat()
            elif task.completed_at:
                completed_at = task.completed_at.isoformat()

            conn.execute("""
                UPDATE tasks SET
                title = ?, description = ?, status = ?, priority = ?,
                due_date = ?, tags = ?, assigned_to = ?, completed_at = ?
                WHERE id = ?
            """, (
                task.title, task.description, task.status.value, task.priority.value,
                task.due_date.isoformat() if task.due_date else None,
                json.dumps(task.tags or []), task.assigned_to,
                completed_at, task_id
            ))
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def delete_task(self, task_id: int) -> bool:
        conn = self.db.get_connection()
        try:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def _row_to_task(self, row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=TaskStatus(row["status"]),
            priority=TaskPriority(row["priority"]),
            due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            tags=json.loads(row["tags"]),
            assigned_to=row["assigned_to"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        )

class ContactService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_contact(self, contact: Contact) -> int:
        conn = self.db.get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO contacts
                (name, email, phone, address, company, birthday, notes, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contact.name, contact.email, contact.phone, contact.address,
                contact.company, contact.birthday, contact.notes,
                json.dumps(contact.tags or [])
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_contacts(self, search: str = None, limit: int = 100) -> List[Contact]:
        conn = self.db.get_connection()
        try:
            if search:
                query = """SELECT * FROM contacts
                          WHERE name LIKE ? OR email LIKE ? OR company LIKE ?
                          ORDER BY name LIMIT ?"""
                search_term = f"%{search}%"
                params = [search_term, search_term, search_term, limit]
            else:
                query = "SELECT * FROM contacts ORDER BY name LIMIT ?"
                params = [limit]

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_contact(row) for row in rows]
        finally:
            conn.close()

    def get_contact(self, contact_id: int) -> Optional[Contact]:
        conn = self.db.get_connection()
        try:
            row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
            return self._row_to_contact(row) if row else None
        finally:
            conn.close()

    def update_contact(self, contact_id: int, contact: Contact) -> bool:
        conn = self.db.get_connection()
        try:
            conn.execute("""
                UPDATE contacts SET
                name = ?, email = ?, phone = ?, address = ?,
                company = ?, birthday = ?, notes = ?, tags = ?
                WHERE id = ?
            """, (
                contact.name, contact.email, contact.phone, contact.address,
                contact.company, contact.birthday, contact.notes,
                json.dumps(contact.tags or []), contact_id
            ))
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def delete_contact(self, contact_id: int) -> bool:
        conn = self.db.get_connection()
        try:
            conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def _row_to_contact(self, row) -> Contact:
        return Contact(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            phone=row["phone"],
            address=row["address"],
            company=row["company"],
            birthday=row["birthday"],
            notes=row["notes"],
            tags=json.loads(row["tags"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        )

class FileService:
    def __init__(self, files_root: str):
        self.files_root = Path(files_root)
        self.files_root.mkdir(parents=True, exist_ok=True)

    def list_files(self, path: str = "") -> List[FileInfo]:
        """List files in directory with safety checks"""
        try:
            # Normalize and validate path
            safe_path = self._validate_path(path)
            full_path = self.files_root / safe_path

            if not full_path.exists():
                return []

            files = []
            for item in full_path.iterdir():
                try:
                    stat = item.stat()
                    mime_type, _ = mimetypes.guess_type(str(item))

                    files.append(FileInfo(
                        name=item.name,
                        path=str(item.relative_to(self.files_root)),
                        size=stat.st_size,
                        modified_time=datetime.fromtimestamp(stat.st_mtime),
                        mime_type=mime_type or "application/octet-stream",
                        is_directory=item.is_dir()
                    ))
                except Exception as e:
                    logger.warning(f"Error accessing file {item}: {e}")
                    continue

            return sorted(files, key=lambda x: (not x.is_directory, x.name.lower()))

        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []

    def get_file_info(self, path: str) -> Optional[FileInfo]:
        """Get file information"""
        try:
            safe_path = self._validate_path(path)
            full_path = self.files_root / safe_path

            if not full_path.exists():
                return None

            stat = full_path.stat()
            mime_type, _ = mimetypes.guess_type(str(full_path))

            return FileInfo(
                name=full_path.name,
                path=str(full_path.relative_to(self.files_root)),
                size=stat.st_size,
                modified_time=datetime.fromtimestamp(stat.st_mtime),
                mime_type=mime_type or "application/octet-stream",
                is_directory=full_path.is_dir()
            )

        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None

    def _validate_path(self, path: str) -> Path:
        """Validate and normalize path to prevent directory traversal"""
        if not path:
            return Path(".")

        # Remove any dangerous components
        path = path.replace("..", "").replace("//", "/")

        # Normalize path
        normalized = Path(path).as_posix()
        if normalized.startswith("/"):
            normalized = normalized[1:]

        return Path(normalized)

# Background Services
class ReminderService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    async def check_reminders(self):
        """Check for upcoming reminders"""
        try:
            conn = self.db.get_connection()

            # Check for event reminders
            now = datetime.now()
            reminder_window = now + timedelta(minutes=30)  # Check next 30 minutes

            events = conn.execute("""
                SELECT id, title, start_time, reminder_minutes
                FROM calendar_events
                WHERE start_time BETWEEN ? AND ?
                AND reminder_minutes IS NOT NULL
            """, (now.isoformat(), reminder_window.isoformat())).fetchall()

            for event in events:
                reminder_time = datetime.fromisoformat(event["start_time"]) - timedelta(minutes=event["reminder_minutes"])

                if now >= reminder_time:
                    # Check if reminder already sent
                    existing = conn.execute("""
                        SELECT id FROM reminders
                        WHERE event_id = ? AND sent = TRUE
                    """, (event["id"],)).fetchone()

                    if not existing:
                        # Create reminder
                        conn.execute("""
                            INSERT INTO reminders (event_id, reminder_time, message, sent)
                            VALUES (?, ?, ?, TRUE)
                        """, (
                            event["id"],
                            reminder_time.isoformat(),
                            f"Reminder: {event['title']} starting at {event['start_time']}"
                        ))

                        logger.info(f"Reminder sent for event: {event['title']}")

            # Check for overdue tasks
            overdue_tasks = conn.execute("""
                SELECT id, title, due_date
                FROM tasks
                WHERE due_date < ? AND status NOT IN ('completed', 'cancelled')
            """, (now.isoformat(),)).fetchall()

            for task in overdue_tasks:
                logger.info(f"Overdue task: {task['title']}")

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error checking reminders: {e}")

# Global services
db_manager = DatabaseManager(DB_PATH)
calendar_service = CalendarService(db_manager)
task_service = TaskService(db_manager)
contact_service = ContactService(db_manager)
file_service = FileService(FILES_ROOT)
llm_service = LLMService()
reminder_service = ReminderService(db_manager)

# Scheduler for background tasks
scheduler = AsyncIOScheduler()

async def startup_tasks():
    """Tasks to run on startup"""
    logger.info("Starting background scheduler")

    # Schedule reminder checks
    scheduler.add_job(
        reminder_service.check_reminders,
        'interval',
        minutes=REMINDER_CHECK_MINUTES,
        id='reminder_check'
    )

    # Schedule daily review (placeholder)
    scheduler.add_job(
        lambda: logger.info("Daily review time"),
        'cron',
        hour=DAILY_REVIEW_HOUR,
        id='daily_review'
    )

    scheduler.start()

async def shutdown_tasks():
    """Tasks to run on shutdown"""
    logger.info("Shutting down scheduler")
    scheduler.shutdown()

# FastAPI lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_tasks()
    yield
    # Shutdown
    await shutdown_tasks()

# FastAPI app
app = FastAPI(
    title="Personal Data Management Service",
    description="Standalone service for calendar, tasks, contacts, and file management",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "connected",
            "scheduler": "running" if scheduler.running else "stopped",
            "llm": "available" if (ANTHROPIC_API_KEY or OPENAI_API_KEY) else "fallback"
        }
    }

# Calendar endpoints
@app.post("/calendar/events")
async def create_event(event: CalendarEvent):
    """Create a new calendar event"""
    try:
        event_id = calendar_service.create_event(event)
        return {"event_id": event_id, "message": "Event created successfully"}
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calendar/events")
async def get_events(
    start: Optional[datetime] = Query(None, description="Start time filter"),
    end: Optional[datetime] = Query(None, description="End time filter")
):
    """Get calendar events with optional time filters"""
    try:
        events = calendar_service.get_events(start, end)
        return {"events": events, "count": len(events)}
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calendar/today")
async def get_today_events():
    """Get today's calendar events"""
    try:
        events = calendar_service.get_today_events()
        return {"events": events, "count": len(events), "date": datetime.now().date().isoformat()}
    except Exception as e:
        logger.error(f"Error getting today's events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calendar/events/{event_id}")
async def get_event(event_id: int):
    """Get a specific calendar event"""
    event = calendar_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"event": event}

@app.put("/calendar/events/{event_id}")
async def update_event(event_id: int, event: CalendarEvent):
    """Update a calendar event"""
    try:
        success = calendar_service.update_event(event_id, event)
        if not success:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"message": "Event updated successfully"}
    except Exception as e:
        logger.error(f"Error updating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/calendar/events/{event_id}")
async def delete_event(event_id: int):
    """Delete a calendar event"""
    try:
        success = calendar_service.delete_event(event_id)
        if not success:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"message": "Event deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Task endpoints
@app.post("/tasks")
async def create_task(task: Task):
    """Create a new task"""
    try:
        task_id = task_service.create_task(task)
        return {"task_id": task_id, "message": "Task created successfully"}
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks")
async def get_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of tasks to return")
):
    """Get tasks with optional filters"""
    try:
        tasks = task_service.get_tasks(status, limit)
        return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    """Get a specific task"""
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task}

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: Task):
    """Update a task"""
    try:
        success = task_service.update_task(task_id, task)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task updated successfully"}
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """Delete a task"""
    try:
        success = task_service.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Contact endpoints
@app.post("/contacts")
async def create_contact(contact: Contact):
    """Create a new contact"""
    try:
        contact_id = contact_service.create_contact(contact)
        return {"contact_id": contact_id, "message": "Contact created successfully"}
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contacts")
async def get_contacts(
    search: Optional[str] = Query(None, description="Search by name, email, or company"),
    limit: int = Query(100, description="Maximum number of contacts to return")
):
    """Get contacts with optional search"""
    try:
        contacts = contact_service.get_contacts(search, limit)
        return {"contacts": contacts, "count": len(contacts)}
    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contacts/{contact_id}")
async def get_contact(contact_id: int):
    """Get a specific contact"""
    contact = contact_service.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"contact": contact}

@app.put("/contacts/{contact_id}")
async def update_contact(contact_id: int, contact: Contact):
    """Update a contact"""
    try:
        success = contact_service.update_contact(contact_id, contact)
        if not success:
            raise HTTPException(status_code=404, detail="Contact not found")
        return {"message": "Contact updated successfully"}
    except Exception as e:
        logger.error(f"Error updating contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: int):
    """Delete a contact"""
    try:
        success = contact_service.delete_contact(contact_id)
        if not success:
            raise HTTPException(status_code=404, detail="Contact not found")
        return {"message": "Contact deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# File management endpoints
@app.get("/files")
async def list_files(path: str = Query("", description="Directory path to list")):
    """List files in directory"""
    try:
        files = file_service.list_files(path)
        return {"files": files, "count": len(files), "path": path}
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/info")
async def get_file_info(path: str = Query(..., description="File path")):
    """Get file information"""
    try:
        file_info = file_service.get_file_info(path)
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        return {"file": file_info}
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Natural language processing endpoint
@app.post("/process/natural")
async def process_natural_language(request: NaturalLanguageRequest):
    """Process natural language requests"""
    try:
        # Parse the natural language
        parsed = await llm_service.parse_natural_language(request.text, request.context)

        # Execute the parsed command
        result = await execute_parsed_command(parsed)

        return {
            "parsed": parsed,
            "result": result,
            "response": parsed.get("response", "Command processed")
        }

    except Exception as e:
        logger.error(f"Error processing natural language: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def execute_parsed_command(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a parsed command"""
    try:
        command_type = parsed.get("type")
        action = parsed.get("action")
        data = parsed.get("data", {})

        if command_type == "calendar_event" and action == "create":
            # Create calendar event
            event = CalendarEvent(**data)
            event_id = calendar_service.create_event(event)
            return {"type": "calendar_event", "id": event_id, "action": "created"}

        elif command_type == "task" and action == "create":
            # Create task
            task = Task(**data)
            task_id = task_service.create_task(task)
            return {"type": "task", "id": task_id, "action": "created"}

        elif command_type == "contact" and action == "create":
            # Create contact
            contact = Contact(**data)
            contact_id = contact_service.create_contact(contact)
            return {"type": "contact", "id": contact_id, "action": "created"}

        elif command_type == "query":
            # Handle queries
            query = data.get("query", "")
            if "today" in query.lower():
                events = calendar_service.get_today_events()
                tasks = task_service.get_tasks(TaskStatus.pending, 5)
                return {
                    "type": "query",
                    "data": {
                        "events": [e.dict() for e in events],
                        "tasks": [t.dict() for t in tasks]
                    }
                }

        return {"type": "unknown", "message": "Command not recognized"}

    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return {"type": "error", "message": str(e)}

# Summary endpoints
@app.get("/summary/today")
async def get_today_summary():
    """Get today's summary of events and tasks"""
    try:
        events = calendar_service.get_today_events()
        pending_tasks = task_service.get_tasks(TaskStatus.pending, 10)

        return {
            "date": datetime.now().date().isoformat(),
            "events": {
                "count": len(events),
                "items": events
            },
            "tasks": {
                "pending_count": len(pending_tasks),
                "items": pending_tasks[:5]  # Show only first 5
            }
        }
    except Exception as e:
        logger.error(f"Error getting today's summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_statistics():
    """Get service statistics"""
    try:
        conn = db_manager.get_connection()

        # Get counts
        event_count = conn.execute("SELECT COUNT(*) FROM calendar_events").fetchone()[0]
        task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        contact_count = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]

        # Get pending tasks
        pending_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'").fetchone()[0]

        # Get today's events
        today = datetime.now().date()
        today_events = conn.execute("""
            SELECT COUNT(*) FROM calendar_events
            WHERE date(start_time) = ?
        """, (today.isoformat(),)).fetchone()[0]

        conn.close()

        return {
            "total_events": event_count,
            "total_tasks": task_count,
            "total_contacts": contact_count,
            "pending_tasks": pending_tasks,
            "today_events": today_events,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)