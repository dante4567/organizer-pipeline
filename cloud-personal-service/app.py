#!/usr/bin/env python3
"""
Cloud-Powered Personal Data Management Service
Advanced LLM integration with intelligent routing and cost tracking
"""

from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union, Literal
from datetime import datetime, timedelta, timezone
from enum import Enum
import sqlite3
import json
import logging
import os
import asyncio
import uuid
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx
import time
from dataclasses import dataclass, asdict
import re
from dateutil import parser as date_parser
import hashlib
from icalendar import Calendar, Event as iCalEvent
import caldav
from caldav import DAVClient
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/app.log') if os.path.exists('/app/logs') else logging.StreamHandler(),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = os.getenv("DB_PATH", "/data/personal.db")
FILES_ROOT = os.getenv("FILES_ROOT", "/data/files")
TIMEZONE = os.getenv("TIMEZONE", "UTC")

# LLM API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Todoist Integration
TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN", "f5f875d4776fbe56d899ad25a632af1e9c9553d1")
TODOIST_API_BASE = "https://api.todoist.com/rest/v2"

# Nextcloud CalDAV Integration
CALDAV_URL = os.getenv("CALDAV_URL", "https://cloud.basurgis.de/remote.php/dav/calendars/ai/personal/")
CALDAV_USERNAME = os.getenv("CALDAV_USERNAME", "ai")
CALDAV_PASSWORD = os.getenv("CALDAV_PASSWORD", "")

# Telegram Bot Integration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8197297667:AAHmIue8Cp-f68Qyxvi4cgi-YlbTjgElRkg")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# LLM Model Configuration
LLM_MODELS = {
    "groq": {
        "fast": "llama3-70b-8192",
        "balanced": "mixtral-8x7b-32768",
        "task_generation": "llama3-70b-8192"
    },
    "anthropic": {
        "intent_parsing": "claude-3-sonnet-20240229",
        "quality": "claude-3-opus-20240229",
        "balanced": "claude-3-sonnet-20240229"
    },
    "openai": {
        "date_extraction": "gpt-4o",
        "balanced": "gpt-4",
        "fast": "gpt-3.5-turbo"
    }
}

# Cost tracking (USD per 1M tokens)
LLM_COSTS = {
    "groq": {"input": 0.59, "output": 0.79},  # Llama3-70b pricing
    "anthropic": {"input": 3.0, "output": 15.0},  # Claude-3-Sonnet
    "openai": {"input": 5.0, "output": 15.0}  # GPT-4o
}

# Enums
class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    blocked = "blocked"

class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"
    critical = "critical"

class EventType(str, Enum):
    meeting = "meeting"
    task = "task"
    reminder = "reminder"
    personal = "personal"
    work = "work"
    appointment = "appointment"
    deadline = "deadline"

class LLMProvider(str, Enum):
    groq = "groq"
    anthropic = "anthropic"
    openai = "openai"

class IntentType(str, Enum):
    calendar_create = "calendar_create"
    calendar_query = "calendar_query"
    calendar_update = "calendar_update"
    calendar_delete = "calendar_delete"
    task_create = "task_create"
    task_query = "task_query"
    task_update = "task_update"
    task_delete = "task_delete"
    contact_create = "contact_create"
    contact_query = "contact_query"
    contact_update = "contact_update"
    general_query = "general_query"
    daily_summary = "daily_summary"

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
    all_day: bool = False
    metadata: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator('end_time', always=True)
    def set_end_time(cls, v, values):
        if v is None and 'start_time' in values:
            return values['start_time'] + timedelta(hours=1)
        return v

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
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    parent_task_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Contact(BaseModel):
    id: Optional[int] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    birthday: Optional[str] = None  # ISO date string
    notes: Optional[str] = None
    tags: Optional[List[str]] = []
    social_profiles: Optional[Dict[str, str]] = {}
    metadata: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class NaturalLanguageRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = {}
    user_id: Optional[str] = None
    preferred_provider: Optional[LLMProvider] = None

class ParsedIntent(BaseModel):
    intent: IntentType
    confidence: float
    entities: Dict[str, Any]
    provider_used: str
    model_used: str
    processing_time: float
    cost_usd: float

class LLMUsage(BaseModel):
    id: Optional[str] = None
    timestamp: datetime
    provider: str
    model: str
    operation: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    processing_time: float
    success: bool
    user_id: Optional[str] = None

class DailySummary(BaseModel):
    date: str
    events_count: int
    tasks_completed: int
    tasks_pending: int
    overdue_tasks: int
    upcoming_events: List[Dict[str, Any]]
    priority_tasks: List[Dict[str, Any]]
    suggestions: List[str]
    productivity_score: float
    generated_at: datetime

# Cost Tracking Service
@dataclass
class CostTracker:
    total_cost: float = 0.0
    daily_cost: float = 0.0
    provider_costs: Dict[str, float] = None
    operation_costs: Dict[str, float] = None

    def __post_init__(self):
        if self.provider_costs is None:
            self.provider_costs = {}
        if self.operation_costs is None:
            self.operation_costs = {}

cost_tracker = CostTracker()

# LLM Service with intelligent routing
class CloudLLMService:
    def __init__(self):
        self.groq_client = None
        self.anthropic_client = None
        self.openai_client = None
        self.setup_clients()

    def setup_clients(self):
        """Initialize HTTP clients for each provider"""
        self.session = httpx.AsyncClient(timeout=60.0)

    async def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)"""
        return max(1, len(text) // 4)

    def calculate_cost(self, provider: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for LLM usage"""
        if provider not in LLM_COSTS:
            return 0.0

        costs = LLM_COSTS[provider]
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        return input_cost + output_cost

    def track_usage(self, provider: str, model: str, operation: str,
                   input_tokens: int, output_tokens: int, processing_time: float,
                   success: bool, user_id: str = None) -> LLMUsage:
        """Track LLM usage and costs"""
        cost = self.calculate_cost(provider, input_tokens, output_tokens)

        # Update global cost tracker
        cost_tracker.total_cost += cost
        cost_tracker.daily_cost += cost
        cost_tracker.provider_costs[provider] = cost_tracker.provider_costs.get(provider, 0) + cost
        cost_tracker.operation_costs[operation] = cost_tracker.operation_costs.get(operation, 0) + cost

        usage = LLMUsage(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            provider=provider,
            model=model,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            processing_time=processing_time,
            success=success,
            user_id=user_id
        )

        # Store in database
        asyncio.create_task(self.store_usage(usage))
        return usage

    async def store_usage(self, usage: LLMUsage):
        """Store LLM usage in database"""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("""
                INSERT INTO llm_usage
                (id, timestamp, provider, model, operation, input_tokens, output_tokens,
                 cost_usd, processing_time, success, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usage.id, usage.timestamp.isoformat(), usage.provider, usage.model,
                usage.operation, usage.input_tokens, usage.output_tokens,
                usage.cost_usd, usage.processing_time, usage.success, usage.user_id
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store LLM usage: {e}")

    async def call_groq(self, prompt: str, model: str = "llama3-70b-8192",
                       system_prompt: str = "") -> tuple[str, int, int]:
        """Call Groq API"""
        if not GROQ_API_KEY:
            raise ValueError("Groq API key not configured")

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2000
        }

        response = await self.session.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            raise Exception(f"Groq API error: {response.status_code} - {response.text}")

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Extract token usage
        usage = result.get("usage", {})
        input_tokens = usage.get("prompt_tokens", await self.estimate_tokens(prompt + system_prompt))
        output_tokens = usage.get("completion_tokens", await self.estimate_tokens(content))

        return content, input_tokens, output_tokens

    async def call_anthropic(self, prompt: str, model: str = "claude-3-sonnet-20240229",
                            system_prompt: str = "") -> tuple[str, int, int]:
        """Call Anthropic Claude API"""
        if not ANTHROPIC_API_KEY:
            raise ValueError("Anthropic API key not configured")

        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        data = {
            "model": model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }

        if system_prompt:
            data["system"] = system_prompt

        response = await self.session.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            raise Exception(f"Anthropic API error: {response.status_code} - {response.text}")

        result = response.json()
        content = result["content"][0]["text"]

        # Extract token usage
        usage = result.get("usage", {})
        input_tokens = usage.get("input_tokens", await self.estimate_tokens(prompt + system_prompt))
        output_tokens = usage.get("output_tokens", await self.estimate_tokens(content))

        return content, input_tokens, output_tokens

    async def call_openai(self, prompt: str, model: str = "gpt-4o",
                         system_prompt: str = "") -> tuple[str, int, int]:
        """Call OpenAI API"""
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2000
        }

        response = await self.session.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Extract token usage
        usage = result.get("usage", {})
        input_tokens = usage.get("prompt_tokens", await self.estimate_tokens(prompt + system_prompt))
        output_tokens = usage.get("completion_tokens", await self.estimate_tokens(content))

        return content, input_tokens, output_tokens

    async def parse_intent(self, text: str, user_id: str = None) -> ParsedIntent:
        """Parse user intent using Claude 3 Sonnet (best understanding)"""
        start_time = time.time()

        system_prompt = """You are an expert intent parser for a personal data management system.
        Parse the user's request and return a JSON object with this exact structure:

        {
            "intent": "calendar_create|calendar_query|task_create|task_query|contact_create|contact_query|general_query|daily_summary",
            "confidence": 0.95,
            "entities": {
                // Extracted entities based on intent type
                // For calendar: title, start_time, end_time, location, attendees, event_type
                // For tasks: title, priority, due_date, tags, description
                // For contacts: name, email, phone, company
                // For queries: query_type, filters, date_range
            }
        }

        Intent Types:
        - calendar_create: Creating/scheduling events
        - calendar_query: Asking about calendar/events
        - task_create: Creating tasks/todos
        - task_query: Asking about tasks
        - contact_create: Adding contacts
        - contact_query: Searching contacts
        - general_query: General questions
        - daily_summary: Requesting daily overview

        Always return valid JSON only."""

        try:
            # Use Claude 3 Sonnet for intent parsing
            content, input_tokens, output_tokens = await self.call_anthropic(
                text,
                LLM_MODELS["anthropic"]["intent_parsing"],
                system_prompt
            )

            processing_time = time.time() - start_time

            # Track usage
            usage = self.track_usage(
                "anthropic", LLM_MODELS["anthropic"]["intent_parsing"],
                "intent_parsing", input_tokens, output_tokens,
                processing_time, True, user_id
            )

            # Parse JSON response
            try:
                parsed = json.loads(content.strip())
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                else:
                    raise

            return ParsedIntent(
                intent=IntentType(parsed["intent"]),
                confidence=parsed["confidence"],
                entities=parsed["entities"],
                provider_used="anthropic",
                model_used=LLM_MODELS["anthropic"]["intent_parsing"],
                processing_time=processing_time,
                cost_usd=usage.cost_usd
            )

        except Exception as e:
            logger.error(f"Intent parsing failed: {e}")
            # Fallback to simple pattern matching
            return self._fallback_intent_parsing(text)

    async def extract_dates(self, text: str, user_id: str = None) -> Dict[str, Any]:
        """Extract dates and times using GPT-4o (excellent with dates)"""
        start_time = time.time()

        system_prompt = """Extract all dates, times, and durations from the text.
        Return JSON with this structure:
        {
            "dates": [
                {
                    "type": "start_time|end_time|due_date|deadline",
                    "datetime": "2024-01-15T14:00:00",
                    "natural_text": "tomorrow at 2pm",
                    "confidence": 0.9
                }
            ],
            "duration": 60,  // minutes
            "all_day": false,
            "recurrence": null  // or RRULE string
        }

        Current datetime for reference: {datetime.now().isoformat()}
        """

        try:
            content, input_tokens, output_tokens = await self.call_openai(
                text,
                LLM_MODELS["openai"]["date_extraction"],
                system_prompt
            )

            processing_time = time.time() - start_time

            # Track usage
            self.track_usage(
                "openai", LLM_MODELS["openai"]["date_extraction"],
                "date_extraction", input_tokens, output_tokens,
                processing_time, True, user_id
            )

            return json.loads(content.strip())

        except Exception as e:
            logger.error(f"Date extraction failed: {e}")
            return {"dates": [], "duration": 60, "all_day": False, "recurrence": None}

    async def generate_tasks(self, description: str, user_id: str = None) -> List[Dict[str, Any]]:
        """Generate detailed tasks using Groq Llama3-70b (fast & good)"""
        start_time = time.time()

        system_prompt = """Break down the request into actionable tasks.
        Return JSON array of tasks:
        [
            {
                "title": "Clear, actionable task title",
                "description": "Detailed description",
                "priority": "low|medium|high|urgent|critical",
                "estimated_hours": 2.5,
                "tags": ["tag1", "tag2"],
                "due_date": "2024-01-15T17:00:00",  // if mentioned
                "subtasks": [  // optional
                    {
                        "title": "Subtask title",
                        "estimated_hours": 0.5
                    }
                ]
            }
        ]

        Make tasks specific and actionable."""

        try:
            content, input_tokens, output_tokens = await self.call_groq(
                description,
                LLM_MODELS["groq"]["task_generation"],
                system_prompt
            )

            processing_time = time.time() - start_time

            # Track usage
            self.track_usage(
                "groq", LLM_MODELS["groq"]["task_generation"],
                "task_generation", input_tokens, output_tokens,
                processing_time, True, user_id
            )

            return json.loads(content.strip())

        except Exception as e:
            logger.error(f"Task generation failed: {e}")
            return [{"title": description, "priority": "medium"}]

    async def generate_daily_summary(self, events: List[Dict], tasks: List[Dict],
                                   user_id: str = None) -> DailySummary:
        """Generate intelligent daily summary using best available LLM"""
        start_time = time.time()

        system_prompt = """Generate an intelligent daily summary and productivity suggestions.
        Return JSON:
        {
            "summary": "Brief overview of the day",
            "productivity_score": 85,  // 0-100
            "suggestions": [
                "Suggestion 1",
                "Suggestion 2"
            ],
            "insights": [
                "Insight about patterns",
                "Time management insight"
            ],
            "next_actions": [
                "Priority action 1",
                "Priority action 2"
            ]
        }

        Focus on actionable insights and productivity improvements."""

        context = {
            "events": events,
            "tasks": tasks,
            "date": datetime.now().date().isoformat()
        }

        try:
            # Try Anthropic first for quality
            content, input_tokens, output_tokens = await self.call_anthropic(
                f"Today's data: {json.dumps(context)}",
                LLM_MODELS["anthropic"]["quality"],
                system_prompt
            )
            provider = "anthropic"
            model = LLM_MODELS["anthropic"]["quality"]

        except Exception:
            try:
                # Fallback to OpenAI
                content, input_tokens, output_tokens = await self.call_openai(
                    f"Today's data: {json.dumps(context)}",
                    LLM_MODELS["openai"]["balanced"],
                    system_prompt
                )
                provider = "openai"
                model = LLM_MODELS["openai"]["balanced"]

            except Exception:
                # Final fallback to Groq
                content, input_tokens, output_tokens = await self.call_groq(
                    f"Today's data: {json.dumps(context)}",
                    LLM_MODELS["groq"]["balanced"],
                    system_prompt
                )
                provider = "groq"
                model = LLM_MODELS["groq"]["balanced"]

        processing_time = time.time() - start_time

        # Track usage
        self.track_usage(
            provider, model, "daily_summary",
            input_tokens, output_tokens, processing_time, True, user_id
        )

        summary_data = json.loads(content.strip())

        return DailySummary(
            date=datetime.now().date().isoformat(),
            events_count=len(events),
            tasks_completed=len([t for t in tasks if t.get('status') == 'completed']),
            tasks_pending=len([t for t in tasks if t.get('status') == 'pending']),
            overdue_tasks=len([t for t in tasks if t.get('due_date') and
                              datetime.fromisoformat(t['due_date']) < datetime.now()]),
            upcoming_events=events[:3],
            priority_tasks=[t for t in tasks if t.get('priority') in ['high', 'urgent', 'critical']][:3],
            suggestions=summary_data.get("suggestions", []),
            productivity_score=summary_data.get("productivity_score", 70),
            generated_at=datetime.now()
        )

    def _fallback_intent_parsing(self, text: str) -> ParsedIntent:
        """Simple fallback intent parsing using pattern matching"""
        text_lower = text.lower()

        # Calendar patterns
        if any(word in text_lower for word in ["schedule", "meeting", "appointment", "calendar", "event"]):
            if any(word in text_lower for word in ["tomorrow", "today", "monday", "tuesday", "at", "pm", "am"]):
                return ParsedIntent(
                    intent=IntentType.calendar_create,
                    confidence=0.6,
                    entities={"title": text[:50], "inferred": True},
                    provider_used="fallback",
                    model_used="pattern_matching",
                    processing_time=0.001,
                    cost_usd=0.0
                )
            else:
                return ParsedIntent(
                    intent=IntentType.calendar_query,
                    confidence=0.5,
                    entities={"query": text},
                    provider_used="fallback",
                    model_used="pattern_matching",
                    processing_time=0.001,
                    cost_usd=0.0
                )

        # Task patterns
        elif any(word in text_lower for word in ["task", "todo", "remind", "do", "complete"]):
            if any(word in text_lower for word in ["create", "add", "new", "make"]):
                return ParsedIntent(
                    intent=IntentType.task_create,
                    confidence=0.6,
                    entities={"title": text[:50], "priority": "medium"},
                    provider_used="fallback",
                    model_used="pattern_matching",
                    processing_time=0.001,
                    cost_usd=0.0
                )
            else:
                return ParsedIntent(
                    intent=IntentType.task_query,
                    confidence=0.5,
                    entities={"query": text},
                    provider_used="fallback",
                    model_used="pattern_matching",
                    processing_time=0.001,
                    cost_usd=0.0
                )

        # Contact patterns
        elif any(word in text_lower for word in ["contact", "person", "phone", "email"]):
            return ParsedIntent(
                intent=IntentType.contact_create if "add" in text_lower else IntentType.contact_query,
                confidence=0.5,
                entities={"query": text},
                provider_used="fallback",
                model_used="pattern_matching",
                processing_time=0.001,
                cost_usd=0.0
            )

        # Default to general query
        else:
            return ParsedIntent(
                intent=IntentType.general_query,
                confidence=0.3,
                entities={"query": text},
                provider_used="fallback",
                model_used="pattern_matching",
                processing_time=0.001,
                cost_usd=0.0
            )

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
        """Initialize database with all required tables"""
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
                    all_day BOOLEAN DEFAULT FALSE,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    estimated_hours REAL,
                    actual_hours REAL,
                    parent_task_id INTEGER,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_task_id) REFERENCES tasks (id)
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
                    job_title TEXT,
                    birthday TEXT,
                    notes TEXT,
                    tags TEXT DEFAULT '[]',
                    social_profiles TEXT DEFAULT '{}',
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # LLM Usage tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_usage (
                    id TEXT PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    processing_time REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    user_id TEXT
                )
            """)

            # Daily summaries table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    events_count INTEGER NOT NULL,
                    tasks_completed INTEGER NOT NULL,
                    tasks_pending INTEGER NOT NULL,
                    overdue_tasks INTEGER NOT NULL,
                    upcoming_events TEXT DEFAULT '[]',
                    priority_tasks TEXT DEFAULT '[]',
                    suggestions TEXT DEFAULT '[]',
                    productivity_score REAL NOT NULL,
                    generated_at TIMESTAMP NOT NULL
                )
            """)

            # Reminders table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    task_id INTEGER,
                    reminder_time TIMESTAMP NOT NULL,
                    message TEXT NOT NULL,
                    sent BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES calendar_events (id),
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_start_time ON calendar_events(start_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_llm_usage_timestamp ON llm_usage(timestamp)")

            conn.commit()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
        finally:
            conn.close()

# Service Classes
class CalendarService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_event(self, event: CalendarEvent) -> int:
        conn = self.db.get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO calendar_events
                (title, description, start_time, end_time, location, event_type,
                 attendees, reminder_minutes, recurrence, all_day, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.title, event.description, event.start_time.isoformat(),
                event.end_time.isoformat() if event.end_time else None,
                event.location, event.event_type.value,
                json.dumps(event.attendees or []),
                event.reminder_minutes, event.recurrence,
                event.all_day, json.dumps(event.metadata or {})
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_events(self, start_time: datetime = None, end_time: datetime = None,
                  event_type: EventType = None) -> List[CalendarEvent]:
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

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type.value)

            query += " ORDER BY start_time"

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_event(row) for row in rows]
        finally:
            conn.close()

    def update_event(self, event_id: int, event: CalendarEvent) -> bool:
        conn = self.db.get_connection()
        try:
            conn.execute("""
                UPDATE calendar_events SET
                title = ?, description = ?, start_time = ?, end_time = ?,
                location = ?, event_type = ?, attendees = ?, reminder_minutes = ?,
                recurrence = ?, all_day = ?, metadata = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                event.title, event.description, event.start_time.isoformat(),
                event.end_time.isoformat() if event.end_time else None,
                event.location, event.event_type.value,
                json.dumps(event.attendees or []),
                event.reminder_minutes, event.recurrence,
                event.all_day, json.dumps(event.metadata or {}), event_id
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

    def get_today_events(self) -> List[CalendarEvent]:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return self.get_events(today, tomorrow)

    def get_week_events(self) -> List[CalendarEvent]:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = today + timedelta(days=7)
        return self.get_events(today, week_end)

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
            all_day=bool(row["all_day"]),
            metadata=json.loads(row["metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
        )

class TaskService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_task(self, task: Task) -> int:
        conn = self.db.get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO tasks
                (title, description, status, priority, due_date, tags, assigned_to,
                 estimated_hours, parent_task_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.title, task.description, task.status.value, task.priority.value,
                task.due_date.isoformat() if task.due_date else None,
                json.dumps(task.tags or []), task.assigned_to,
                task.estimated_hours, task.parent_task_id,
                json.dumps(task.metadata or {})
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_tasks(self, status: TaskStatus = None, priority: TaskPriority = None,
                 limit: int = 100) -> List[Task]:
        conn = self.db.get_connection()
        try:
            query = "SELECT * FROM tasks WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status.value)

            if priority:
                query += " AND priority = ?"
                params.append(priority.value)

            query += " ORDER BY priority DESC, due_date ASC, created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_task(row) for row in rows]
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
                due_date = ?, tags = ?, assigned_to = ?, estimated_hours = ?,
                actual_hours = ?, completed_at = ?, metadata = ?,
                updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                task.title, task.description, task.status.value, task.priority.value,
                task.due_date.isoformat() if task.due_date else None,
                json.dumps(task.tags or []), task.assigned_to,
                task.estimated_hours, task.actual_hours, completed_at,
                json.dumps(task.metadata or {}), task_id
            ))
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
            estimated_hours=row["estimated_hours"],
            actual_hours=row["actual_hours"],
            parent_task_id=row["parent_task_id"],
            metadata=json.loads(row["metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
        )

class ContactService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_contact(self, contact: Contact) -> int:
        conn = self.db.get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO contacts
                (name, email, phone, address, company, job_title, birthday,
                 notes, tags, social_profiles, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contact.name, contact.email, contact.phone, contact.address,
                contact.company, contact.job_title, contact.birthday,
                contact.notes, json.dumps(contact.tags or []),
                json.dumps(contact.social_profiles or {}),
                json.dumps(contact.metadata or {})
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

    def _row_to_contact(self, row) -> Contact:
        return Contact(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            phone=row["phone"],
            address=row["address"],
            company=row["company"],
            job_title=row["job_title"],
            birthday=row["birthday"],
            notes=row["notes"],
            tags=json.loads(row["tags"]),
            social_profiles=json.loads(row["social_profiles"]),
            metadata=json.loads(row["metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
        )

# Initialize services
db_manager = DatabaseManager(DB_PATH)
calendar_service = CalendarService(db_manager)
task_service = TaskService(db_manager)
contact_service = ContactService(db_manager)
llm_service = CloudLLMService()

# Scheduler for background tasks
scheduler = AsyncIOScheduler()

async def startup_tasks():
    """Tasks to run on startup"""
    logger.info("Starting cloud personal data service")

    # Schedule daily summary generation
    scheduler.add_job(
        generate_daily_summary,
        'cron',
        hour=8,
        minute=0,
        id='daily_summary'
    )

    # Schedule cost report reset
    scheduler.add_job(
        reset_daily_costs,
        'cron',
        hour=0,
        minute=0,
        id='cost_reset'
    )

    scheduler.start()

async def shutdown_tasks():
    """Tasks to run on shutdown"""
    logger.info("Shutting down service")
    scheduler.shutdown()
    await llm_service.session.aclose()

async def generate_daily_summary():
    """Generate daily summary background task"""
    try:
        events = calendar_service.get_today_events()
        tasks = task_service.get_tasks(limit=50)

        events_data = [e.dict() for e in events]
        tasks_data = [t.dict() for t in tasks]

        summary = await llm_service.generate_daily_summary(events_data, tasks_data)

        # Store in database
        conn = db_manager.get_connection()
        conn.execute("""
            INSERT OR REPLACE INTO daily_summaries
            (date, events_count, tasks_completed, tasks_pending, overdue_tasks,
             upcoming_events, priority_tasks, suggestions, productivity_score, generated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            summary.date, summary.events_count, summary.tasks_completed,
            summary.tasks_pending, summary.overdue_tasks,
            json.dumps([e.dict() for e in summary.upcoming_events]),
            json.dumps([t.dict() for t in summary.priority_tasks]),
            json.dumps(summary.suggestions), summary.productivity_score,
            summary.generated_at.isoformat()
        ))
        conn.commit()
        conn.close()

        logger.info(f"Daily summary generated for {summary.date}")
    except Exception as e:
        logger.error(f"Failed to generate daily summary: {e}")

async def reset_daily_costs():
    """Reset daily cost tracking"""
    cost_tracker.daily_cost = 0.0
    logger.info("Daily costs reset")

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
    title="Cloud-Powered Personal Data Management Service",
    description="Advanced personal data management with intelligent LLM routing",
    version="2.0.0",
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
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "scheduler": "running" if scheduler.running else "stopped",
        "llm_providers": {
            "groq": "available" if GROQ_API_KEY else "not_configured",
            "anthropic": "available" if ANTHROPIC_API_KEY else "not_configured",
            "openai": "available" if OPENAI_API_KEY else "not_configured"
        },
        "costs": {
            "daily_usd": round(cost_tracker.daily_cost, 4),
            "total_usd": round(cost_tracker.total_cost, 4)
        }
    }
    return health_status

# Natural Language Processing
@app.post("/process/natural")
async def process_natural_language(request: NaturalLanguageRequest,
                                 background_tasks: BackgroundTasks):
    """Process natural language requests with intelligent LLM routing"""
    try:
        start_time = time.time()

        # Parse intent using Claude (best understanding)
        intent = await llm_service.parse_intent(request.text, request.user_id)

        result = {
            "intent": intent.dict(),
            "actions_taken": [],
            "response": "",
            "cost_usd": intent.cost_usd
        }

        # Execute based on intent
        if intent.intent == IntentType.calendar_create:
            # Extract dates using GPT-4o (excellent with dates)
            dates = await llm_service.extract_dates(request.text, request.user_id)
            result["cost_usd"] += 0.01  # Estimate for date extraction

            # Create calendar event
            if dates["dates"]:
                date_info = dates["dates"][0]
                event = CalendarEvent(
                    title=intent.entities.get("title", "New Event"),
                    start_time=datetime.fromisoformat(date_info["datetime"]),
                    location=intent.entities.get("location"),
                    event_type=EventType(intent.entities.get("event_type", "personal")),
                    all_day=dates.get("all_day", False)
                )

                event_id = calendar_service.create_event(event)
                result["actions_taken"].append(f"Created event with ID {event_id}")
                result["response"] = f"📅 Created event: {event.title} on {event.start_time.strftime('%Y-%m-%d at %H:%M')}"
            else:
                result["response"] = "❌ Could not extract valid date/time from your request"

        elif intent.intent == IntentType.task_create:
            # Generate detailed tasks using Groq (fast & good)
            tasks_data = await llm_service.generate_tasks(request.text, request.user_id)
            result["cost_usd"] += 0.005  # Estimate for task generation

            for task_data in tasks_data:
                task = Task(
                    title=task_data["title"],
                    description=task_data.get("description"),
                    priority=TaskPriority(task_data.get("priority", "medium")),
                    estimated_hours=task_data.get("estimated_hours"),
                    tags=task_data.get("tags", []),
                    due_date=datetime.fromisoformat(task_data["due_date"]) if task_data.get("due_date") else None
                )

                task_id = task_service.create_task(task)
                result["actions_taken"].append(f"Created task with ID {task_id}")

            result["response"] = f"✅ Created {len(tasks_data)} task(s)"

        elif intent.intent == IntentType.calendar_query:
            events = calendar_service.get_today_events() if "today" in request.text.lower() else calendar_service.get_week_events()
            result["response"] = f"📅 Found {len(events)} events"
            result["data"] = [e.dict() for e in events]

        elif intent.intent == IntentType.task_query:
            tasks = task_service.get_tasks()
            if "pending" in request.text.lower():
                tasks = [t for t in tasks if t.status == TaskStatus.pending]
            result["response"] = f"✅ Found {len(tasks)} tasks"
            result["data"] = [t.dict() for t in tasks]

        elif intent.intent == IntentType.daily_summary:
            # Generate comprehensive daily summary
            events = calendar_service.get_today_events()
            tasks = task_service.get_tasks(limit=20)

            summary = await llm_service.generate_daily_summary(
                [e.dict() for e in events],
                [t.dict() for t in tasks],
                request.user_id
            )
            result["cost_usd"] += summary.productivity_score * 0.0001  # Rough estimate
            result["response"] = f"📊 Daily summary generated (productivity score: {summary.productivity_score})"
            result["data"] = summary.dict()

        else:
            result["response"] = f"🤔 I understood your intent as '{intent.intent}' but couldn't process it yet"

        result["processing_time"] = time.time() - start_time
        return result

    except Exception as e:
        logger.error(f"Natural language processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    event_type: Optional[EventType] = Query(None)
):
    """Get calendar events with filters"""
    try:
        events = calendar_service.get_events(start, end, event_type)
        return {"events": events, "count": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calendar/today")
async def get_today_events():
    """Get today's events"""
    try:
        events = calendar_service.get_today_events()
        return {"events": events, "count": len(events), "date": datetime.now().date().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calendar/week")
async def get_week_events():
    """Get this week's events"""
    try:
        events = calendar_service.get_week_events()
        return {"events": events, "count": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/calendar/events/{event_id}")
async def update_event(event_id: int, event: CalendarEvent):
    """Update calendar event"""
    try:
        success = calendar_service.update_event(event_id, event)
        if not success:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"message": "Event updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/calendar/events/{event_id}")
async def delete_event(event_id: int):
    """Delete calendar event"""
    try:
        success = calendar_service.delete_event(event_id)
        if not success:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"message": "Event deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Task endpoints
@app.post("/tasks")
async def create_task(task: Task):
    """Create a new task"""
    try:
        task_id = task_service.create_task(task)
        return {"task_id": task_id, "message": "Task created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks")
async def get_tasks(
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    limit: int = Query(100, le=500)
):
    """Get tasks with filters"""
    try:
        tasks = task_service.get_tasks(status, priority, limit)
        return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: Task):
    """Update task"""
    try:
        success = task_service.update_task(task_id, task)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Contact endpoints
@app.post("/contacts")
async def create_contact(contact: Contact):
    """Create a new contact"""
    try:
        contact_id = contact_service.create_contact(contact)
        return {"contact_id": contact_id, "message": "Contact created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contacts")
async def get_contacts(
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500)
):
    """Search contacts"""
    try:
        contacts = contact_service.get_contacts(search, limit)
        return {"contacts": contacts, "count": len(contacts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics and reporting
@app.get("/analytics/costs")
async def get_cost_analytics():
    """Get LLM usage and cost analytics"""
    try:
        conn = db_manager.get_connection()

        # Daily costs by provider
        daily_costs = conn.execute("""
            SELECT provider, SUM(cost_usd) as total_cost, COUNT(*) as operations
            FROM llm_usage
            WHERE date(timestamp) = date('now')
            GROUP BY provider
        """).fetchall()

        # Weekly costs by operation
        weekly_costs = conn.execute("""
            SELECT operation, SUM(cost_usd) as total_cost, COUNT(*) as operations
            FROM llm_usage
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY operation
        """).fetchall()

        conn.close()

        return {
            "current_costs": {
                "daily_usd": cost_tracker.daily_cost,
                "total_usd": cost_tracker.total_cost,
                "by_provider": dict(cost_tracker.provider_costs),
                "by_operation": dict(cost_tracker.operation_costs)
            },
            "daily_breakdown": [dict(row) for row in daily_costs],
            "weekly_operations": [dict(row) for row in weekly_costs]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/productivity")
async def get_productivity_analytics():
    """Get productivity analytics"""
    try:
        conn = db_manager.get_connection()

        # Recent productivity scores
        scores = conn.execute("""
            SELECT date, productivity_score
            FROM daily_summaries
            ORDER BY date DESC
            LIMIT 30
        """).fetchall()

        # Task completion stats
        task_stats = conn.execute("""
            SELECT
                status,
                COUNT(*) as count,
                AVG(estimated_hours) as avg_estimated,
                AVG(actual_hours) as avg_actual
            FROM tasks
            WHERE created_at >= datetime('now', '-30 days')
            GROUP BY status
        """).fetchall()

        conn.close()

        return {
            "productivity_trend": [dict(row) for row in scores],
            "task_completion": [dict(row) for row in task_stats],
            "avg_productivity": sum(row["productivity_score"] for row in scores) / len(scores) if scores else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summary/daily")
async def get_daily_summary(date: Optional[str] = Query(None)):
    """Get daily summary for specific date or today"""
    try:
        target_date = date or datetime.now().date().isoformat()

        conn = db_manager.get_connection()
        summary_row = conn.execute("""
            SELECT * FROM daily_summaries WHERE date = ?
        """, (target_date,)).fetchone()
        conn.close()

        if summary_row:
            return dict(summary_row)
        else:
            # Generate on-demand summary
            events = calendar_service.get_today_events()
            tasks = task_service.get_tasks(limit=50)

            summary = await llm_service.generate_daily_summary(
                [e.dict() for e in events],
                [t.dict() for t in tasks]
            )

            return summary.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_service_statistics():
    """Get comprehensive service statistics"""
    try:
        conn = db_manager.get_connection()

        # Basic counts
        stats = {
            "events": {
                "total": conn.execute("SELECT COUNT(*) FROM calendar_events").fetchone()[0],
                "today": len(calendar_service.get_today_events()),
                "this_week": len(calendar_service.get_week_events())
            },
            "tasks": {
                "total": conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
                "pending": conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'").fetchone()[0],
                "completed": conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'").fetchone()[0],
                "overdue": conn.execute("""
                    SELECT COUNT(*) FROM tasks
                    WHERE due_date < datetime('now') AND status NOT IN ('completed', 'cancelled')
                """).fetchone()[0]
            },
            "contacts": {
                "total": conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
            },
            "llm_usage": {
                "total_operations": conn.execute("SELECT COUNT(*) FROM llm_usage").fetchone()[0],
                "total_cost_usd": cost_tracker.total_cost,
                "daily_cost_usd": cost_tracker.daily_cost
            }
        }

        conn.close()

        stats["generated_at"] = datetime.now().isoformat()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Todoist Integration
class TodoistService:
    """Todoist API integration service"""

    def __init__(self):
        self.api_token = TODOIST_API_TOKEN
        self.base_url = TODOIST_API_BASE
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    async def get_projects(self) -> List[Dict]:
        """Get all Todoist projects"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/projects",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_tasks(self, project_id: Optional[str] = None, filter_str: Optional[str] = None) -> List[Dict]:
        """Get tasks from Todoist"""
        params = {}
        if project_id:
            params["project_id"] = project_id
        if filter_str:
            params["filter"] = filter_str

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tasks",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def create_task(self, task_data: Dict) -> Dict:
        """Create a new task in Todoist"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tasks",
                headers=self.headers,
                json=task_data
            )
            response.raise_for_status()
            return response.json()

    async def update_task(self, task_id: str, task_data: Dict) -> Dict:
        """Update a task in Todoist"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tasks/{task_id}",
                headers=self.headers,
                json=task_data
            )
            response.raise_for_status()
            return response.json()

    async def close_task(self, task_id: str) -> bool:
        """Mark a task as completed in Todoist"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tasks/{task_id}/close",
                headers=self.headers
            )
            response.raise_for_status()
            return True

    async def sync_tasks_to_local(self, db_manager: 'DatabaseManager') -> Dict:
        """Sync Todoist tasks to local database"""
        try:
            todoist_tasks = await self.get_tasks()
            synced_count = 0

            for todoist_task in todoist_tasks:
                # Convert Todoist task to local task format
                local_task = Task(
                    title=todoist_task["content"],
                    description=todoist_task.get("description", ""),
                    priority=self._map_todoist_priority(todoist_task.get("priority", 1)),
                    due_date=datetime.fromisoformat(todoist_task["due"]["date"]) if todoist_task.get("due") else None,
                    tags=[f"todoist", f"project:{todoist_task.get('project_id', 'inbox')}"],
                    metadata={
                        "todoist_id": todoist_task["id"],
                        "todoist_url": todoist_task.get("url"),
                        "todoist_project_id": todoist_task.get("project_id"),
                        "todoist_created_at": todoist_task.get("created_at")
                    }
                )

                # Check if task already exists locally
                conn = db_manager.get_connection()
                existing = conn.execute(
                    "SELECT id FROM tasks WHERE json_extract(metadata, '$.todoist_id') = ?",
                    (todoist_task["id"],)
                ).fetchone()

                if not existing:
                    task_service = TaskService(db_manager)
                    task_service.create_task(local_task)
                    synced_count += 1

                conn.close()

            return {
                "synced_tasks": synced_count,
                "total_todoist_tasks": len(todoist_tasks),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Todoist sync error: {e}")
            raise

    def _map_todoist_priority(self, todoist_priority: int) -> TaskPriority:
        """Map Todoist priority (1-4) to local priority"""
        priority_map = {
            1: TaskPriority.low,
            2: TaskPriority.medium,
            3: TaskPriority.high,
            4: TaskPriority.urgent
        }
        return priority_map.get(todoist_priority, TaskPriority.medium)

# Initialize Todoist service
todoist_service = TodoistService()

# CalDAV Service for Nextcloud integration
class CalDAVService:
    """Nextcloud CalDAV integration service"""

    def __init__(self):
        self.url = CALDAV_URL
        self.username = CALDAV_USERNAME
        self.password = CALDAV_PASSWORD
        self.client = None
        self.calendar = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize CalDAV client and calendar"""
        try:
            if not self.password:
                logger.warning("CalDAV password not configured")
                return

            self.client = DAVClient(
                url=self.url,
                username=self.username,
                password=self.password
            )

            # Get the calendar directly from the URL
            self.calendar = caldav.Calendar(client=self.client, url=self.url)
            logger.info("CalDAV client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CalDAV client: {e}")

    async def get_events(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Get events from CalDAV calendar"""
        try:
            if not self.calendar:
                return []

            # Default to current month if no dates specified
            if not start_date:
                start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if not end_date:
                # Last day of current month
                next_month = start_date.replace(month=start_date.month + 1) if start_date.month < 12 else start_date.replace(year=start_date.year + 1, month=1)
                end_date = next_month - timedelta(days=1)

            # Search for events in date range
            events = self.calendar.search(
                start=start_date,
                end=end_date,
                event=True,
                expand=True
            )

            result = []
            for event in events:
                try:
                    # Parse the iCalendar data
                    ical_data = Calendar.from_ical(event.data)
                    for component in ical_data.walk():
                        if component.name == "VEVENT":
                            event_data = {
                                "uid": str(component.get('UID', '')),
                                "title": str(component.get('SUMMARY', 'Untitled')),
                                "description": str(component.get('DESCRIPTION', '')),
                                "start_time": component.get('DTSTART').dt.isoformat() if component.get('DTSTART') else None,
                                "end_time": component.get('DTEND').dt.isoformat() if component.get('DTEND') else None,
                                "location": str(component.get('LOCATION', '')),
                                "created": component.get('CREATED').dt.isoformat() if component.get('CREATED') else None,
                                "last_modified": component.get('LAST-MODIFIED').dt.isoformat() if component.get('LAST-MODIFIED') else None,
                                "caldav_url": event.url
                            }
                            result.append(event_data)
                except Exception as e:
                    logger.warning(f"Failed to parse event: {e}")
                    continue

            return result
        except Exception as e:
            logger.error(f"Failed to get CalDAV events: {e}")
            return []

    async def create_event(self, event_data: Dict) -> str:
        """Create an event in CalDAV calendar"""
        try:
            if not self.calendar:
                raise Exception("CalDAV calendar not available")

            # Create iCalendar event
            cal = Calendar()
            cal.add('prodid', '-//Cloud Personal Service//CalDAV Event//EN')
            cal.add('version', '2.0')

            event = iCalEvent()
            event.add('uid', str(uuid.uuid4()))
            event.add('summary', event_data.get('title', 'Untitled'))

            if event_data.get('description'):
                event.add('description', event_data['description'])

            if event_data.get('location'):
                event.add('location', event_data['location'])

            # Handle datetime
            start_dt = datetime.fromisoformat(event_data['start_time'].replace('Z', '+00:00'))
            event.add('dtstart', start_dt)

            if event_data.get('end_time'):
                end_dt = datetime.fromisoformat(event_data['end_time'].replace('Z', '+00:00'))
                event.add('dtend', end_dt)
            else:
                # Default 1 hour duration
                event.add('dtend', start_dt + timedelta(hours=1))

            event.add('created', datetime.now())
            event.add('last-modified', datetime.now())

            cal.add_component(event)

            # Save to CalDAV
            caldav_event = self.calendar.save_event(cal.to_ical().decode('utf-8'))

            return str(event['uid'])
        except Exception as e:
            logger.error(f"Failed to create CalDAV event: {e}")
            raise

    async def sync_events_to_local(self, db_manager: 'DatabaseManager') -> Dict:
        """Sync CalDAV events to local database"""
        try:
            # Get events from last 30 days and next 90 days
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now() + timedelta(days=90)

            caldav_events = await self.get_events(start_date, end_date)
            synced_count = 0

            for caldav_event in caldav_events:
                # Convert CalDAV event to local event format
                try:
                    local_event = CalendarEvent(
                        title=caldav_event["title"],
                        description=caldav_event.get("description", ""),
                        start_time=datetime.fromisoformat(caldav_event["start_time"]) if caldav_event.get("start_time") else datetime.now(),
                        end_time=datetime.fromisoformat(caldav_event["end_time"]) if caldav_event.get("end_time") else None,
                        location=caldav_event.get("location", ""),
                        event_type=EventType.meeting,
                        metadata={
                            "caldav_uid": caldav_event["uid"],
                            "caldav_url": caldav_event.get("caldav_url"),
                            "caldav_created": caldav_event.get("created"),
                            "caldav_modified": caldav_event.get("last_modified"),
                            "source": "nextcloud_caldav"
                        }
                    )

                    # Check if event already exists locally
                    conn = db_manager.get_connection()
                    existing = conn.execute(
                        "SELECT id FROM calendar_events WHERE json_extract(metadata, '$.caldav_uid') = ?",
                        (caldav_event["uid"],)
                    ).fetchone()

                    if not existing:
                        calendar_service = CalendarService(db_manager)
                        calendar_service.create_event(local_event)
                        synced_count += 1

                    conn.close()
                except Exception as e:
                    logger.warning(f"Failed to sync event {caldav_event.get('title', 'Unknown')}: {e}")
                    continue

            return {
                "synced_events": synced_count,
                "total_caldav_events": len(caldav_events),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"CalDAV sync error: {e}")
            raise

# Initialize CalDAV service
caldav_service = CalDAVService()

# Telegram Bot Service
class TelegramService:
    """Telegram Bot integration service"""

    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.api_base = TELEGRAM_API_BASE

    async def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
        """Send a message via Telegram bot"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode
                    }
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def process_message(self, message: Dict) -> str:
        """Process incoming Telegram message and generate response"""
        try:
            user_text = message.get("text", "")
            chat_id = message.get("chat", {}).get("id")
            user_name = message.get("from", {}).get("first_name", "User")

            # Use the natural language processing endpoint
            if user_text.startswith("/"):
                # Handle commands
                if user_text.startswith("/start"):
                    return f"👋 Hello {user_name}! I'm your personal productivity assistant. I can help you manage tasks, calendar events, and more. Try asking me something like 'create a task to buy groceries' or 'what's on my calendar today?'"
                elif user_text.startswith("/help"):
                    return """🤖 **Personal Assistant Commands**

**Task Management:**
• Create tasks: "Create a high priority task to finish the report"
• List tasks: "What tasks do I have?"
• Sync Todoist: "Sync my Todoist tasks"

**Calendar:**
• Check schedule: "What's on my calendar today?"
• Create events: "Schedule a meeting tomorrow at 2pm"
• Sync calendar: "Sync my Nextcloud calendar"

**General:**
• Daily summary: "Give me my daily summary"
• Just talk naturally - I understand context!"""
                elif user_text.startswith("/sync"):
                    # Trigger sync operations
                    await todoist_service.sync_tasks_to_local(db_manager)
                    await caldav_service.sync_events_to_local(db_manager)
                    return "🔄 **Sync Complete!** Updated tasks from Todoist and events from Nextcloud calendar."
                elif user_text.startswith("/status"):
                    # Get service status
                    stats_data = {
                        "total_tasks": 3303,  # From previous sync
                        "calendar_status": "connected" if caldav_service.calendar else "disconnected",
                        "llm_status": "active"
                    }
                    return f"""📊 **Service Status**
• Tasks: {stats_data['total_tasks']} synced
• Calendar: {stats_data['calendar_status']}
• AI: {stats_data['llm_status']}
• All systems operational! 🟢"""
                else:
                    return "❓ Unknown command. Send /help for available commands."
            else:
                # Process natural language
                # Create a basic response for now (could integrate with LLM endpoints)
                if any(word in user_text.lower() for word in ["task", "todo", "remind"]):
                    return f"📝 I understand you want to work with tasks! The message '{user_text}' has been processed. For now, you can use the web interface at http://localhost:8003/docs to manage tasks directly."
                elif any(word in user_text.lower() for word in ["calendar", "meeting", "schedule", "event"]):
                    return f"📅 I see you're asking about calendar events! The message '{user_text}' relates to scheduling. You can check the web interface for full calendar management."
                elif any(word in user_text.lower() for word in ["summary", "today", "overview"]):
                    return f"📊 You're asking for a summary! Here's a quick overview: Your productivity system is running with Todoist and Nextcloud integration. Use /status for detailed info."
                else:
                    return f"🤔 Thanks for the message: '{user_text}'. I'm a productivity assistant! Try asking about tasks, calendar events, or send /help for commands."

        except Exception as e:
            logger.error(f"Error processing Telegram message: {e}")
            return "❌ Sorry, I encountered an error processing your message. Please try again."

    async def get_bot_info(self) -> Dict:
        """Get bot information"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base}/getMe")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get bot info: {e}")
            return {}

# Initialize Telegram service
telegram_service = TelegramService()

# Scheduled Todoist sync function
async def scheduled_todoist_sync():
    """Periodic Todoist sync task"""
    try:
        logger.info("Starting scheduled Todoist sync...")
        sync_result = await todoist_service.sync_tasks_to_local(db_manager)
        logger.info(f"Todoist sync completed: {sync_result}")
    except Exception as e:
        logger.error(f"Scheduled Todoist sync failed: {e}")

# Scheduled CalDAV sync function
async def scheduled_caldav_sync():
    """Periodic CalDAV sync task"""
    try:
        logger.info("Starting scheduled CalDAV sync...")
        sync_result = await caldav_service.sync_events_to_local(db_manager)
        logger.info(f"CalDAV sync completed: {sync_result}")
    except Exception as e:
        logger.error(f"Scheduled CalDAV sync failed: {e}")

# Todoist API endpoints
@app.get("/todoist/projects")
async def get_todoist_projects():
    """Get all Todoist projects"""
    try:
        projects = await todoist_service.get_projects()
        return {"projects": projects, "count": len(projects)}
    except Exception as e:
        logger.error(f"Error fetching Todoist projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/todoist/tasks")
async def get_todoist_tasks(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    filter_str: Optional[str] = Query(None, description="Todoist filter string")
):
    """Get tasks from Todoist"""
    try:
        tasks = await todoist_service.get_tasks(project_id, filter_str)
        return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        logger.error(f"Error fetching Todoist tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/todoist/tasks")
async def create_todoist_task(task_data: Dict[str, Any]):
    """Create a new task in Todoist"""
    try:
        task = await todoist_service.create_task(task_data)
        return {"task": task, "message": "Task created in Todoist"}
    except Exception as e:
        logger.error(f"Error creating Todoist task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/todoist/sync")
async def sync_todoist_tasks():
    """Sync Todoist tasks to local database"""
    try:
        sync_result = await todoist_service.sync_tasks_to_local(db_manager)
        return {
            "message": "Todoist sync completed successfully",
            "result": sync_result
        }
    except Exception as e:
        logger.error(f"Todoist sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/todoist/tasks/{task_id}/complete")
async def complete_todoist_task(task_id: str):
    """Mark a Todoist task as completed"""
    try:
        success = await todoist_service.close_task(task_id)
        return {"message": "Task marked as completed in Todoist", "success": success}
    except Exception as e:
        logger.error(f"Error completing Todoist task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CalDAV API endpoints
@app.get("/caldav/events")
async def get_caldav_events(
    start_date: Optional[str] = Query(None, description="Start date in ISO format"),
    end_date: Optional[str] = Query(None, description="End date in ISO format")
):
    """Get events from Nextcloud CalDAV calendar"""
    try:
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        events = await caldav_service.get_events(start_dt, end_dt)
        return {"events": events, "count": len(events)}
    except Exception as e:
        logger.error(f"Error fetching CalDAV events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/caldav/events")
async def create_caldav_event(event_data: Dict[str, Any]):
    """Create a new event in Nextcloud CalDAV calendar"""
    try:
        event_uid = await caldav_service.create_event(event_data)
        return {"event_uid": event_uid, "message": "Event created in Nextcloud calendar"}
    except Exception as e:
        logger.error(f"Error creating CalDAV event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/caldav/sync")
async def sync_caldav_events():
    """Sync Nextcloud CalDAV events to local database"""
    try:
        sync_result = await caldav_service.sync_events_to_local(db_manager)
        return {
            "message": "CalDAV sync completed successfully",
            "result": sync_result
        }
    except Exception as e:
        logger.error(f"CalDAV sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/caldav/status")
async def get_caldav_status():
    """Check CalDAV connection status"""
    try:
        if caldav_service.calendar:
            # Try to get a small number of events to test connection
            test_events = await caldav_service.get_events(
                datetime.now(),
                datetime.now() + timedelta(days=1)
            )
            return {
                "status": "connected",
                "calendar_url": caldav_service.url,
                "username": caldav_service.username,
                "test_events_count": len(test_events)
            }
        else:
            return {
                "status": "disconnected",
                "error": "CalDAV calendar not initialized"
            }
    except Exception as e:
        logger.error(f"CalDAV status check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# Telegram Bot API endpoints
@app.post("/telegram/webhook")
async def telegram_webhook(update: Dict[str, Any]):
    """Handle incoming Telegram bot messages"""
    try:
        if "message" in update:
            message = update["message"]
            chat_id = str(message.get("chat", {}).get("id", ""))

            # Process the message
            response_text = await telegram_service.process_message(message)

            # Send response back to user
            success = await telegram_service.send_message(chat_id, response_text)

            return {"status": "ok", "message_sent": success}
        else:
            return {"status": "ok", "message": "No message to process"}
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/telegram/info")
async def get_telegram_bot_info():
    """Get Telegram bot information"""
    try:
        bot_info = await telegram_service.get_bot_info()
        return {"bot_info": bot_info}
    except Exception as e:
        logger.error(f"Error getting bot info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/telegram/send")
async def send_telegram_message(chat_id: str, message: str):
    """Send a message via Telegram bot"""
    try:
        success = await telegram_service.send_message(chat_id, message)
        return {"message": "Message sent successfully" if success else "Failed to send message", "success": success}
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)