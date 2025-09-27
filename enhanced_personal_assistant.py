#!/usr/bin/env python3
"""
Enhanced Personal Assistant with Advanced LLM Integration
Comprehensive organizer-pipeline with multiple providers and features
"""

import json
import re
import uuid
import logging
import asyncio
import aiofiles
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import caldav
from caldav import DAVClient
import vobject
import openai
import requests
from urllib.parse import urljoin
import os
import icalendar
from icalendar import Calendar, Event, Todo, vText
import dateutil.parser
from functools import wraps
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('organizer_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Contact:
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    notes: str = ""
    uid: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class CalendarEvent:
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    description: str = ""
    location: str = ""
    attendees: List[str] = None
    uid: Optional[str] = None
    calendar_name: Optional[str] = None
    recurring: bool = False
    recurrence_rule: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class TodoItem:
    title: str
    description: str = ""
    due_date: Optional[datetime] = None
    priority: str = "normal"
    completed: bool = False
    uid: Optional[str] = None
    tags: List[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class FileActivity:
    filepath: str
    action: str  # created, modified, deleted
    timestamp: datetime
    description: str = ""

class LLMProvider:
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    async def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        openai.api_key = config.get("api_key")
        self.client = openai.AsyncOpenAI(api_key=config.get("api_key"))
    
    async def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.config.get("model", "gpt-4"),
                messages=messages,
                temperature=0.3,
                max_tokens=self.config.get("max_tokens", 2000)
            )
            return response.choices[0].message.content
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e.status_code} - {e.response}")
            raise
        except openai.APITimeoutError as e:
            logger.error(f"OpenAI API timeout error: {e}")
            raise
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected OpenAI error: {e.__class__.__name__}: {e}")
            raise

class OllamaProvider(LLMProvider):
    """Local Ollama provider"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
    
    async def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        try:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:" if system_prompt else prompt
            
            async with aiofiles.open('temp_prompt.txt', 'w') as f:
                await f.write(full_prompt)
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.config.get("model", "llama2"),
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": self.config.get("max_tokens", 2000)
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected Ollama error: {e.__class__.__name__}: {e}")
            raise

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = "https://api.anthropic.com/v1/messages"
    
    async def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        try:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            data = {
                "model": self.config.get("model", "claude-3-sonnet-20240229"),
                "max_tokens": self.config.get("max_tokens", 2000),
                "messages": [{"role": "user", "content": prompt}]
            }
            
            if system_prompt:
                data["system"] = system_prompt
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            return response.json()["content"][0]["text"]
        except requests.exceptions.HTTPError as e:
            logger.error(f"Anthropic HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Anthropic connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected Anthropic error: {e.__class__.__name__}: {e}")
            raise

class DemoProvider(LLMProvider):
    """Demo provider for testing without API keys"""

    def __init__(self, config: Dict):
        super().__init__(config)

    async def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        """Generate demo responses using simple pattern matching"""
        prompt_lower = prompt.lower()
        from datetime import datetime, timedelta
        import json

        if "meeting" in prompt_lower or "appointment" in prompt_lower:
            # Extract basic info from prompt
            title = "Meeting"
            if "with" in prompt_lower:
                parts = prompt_lower.split("with")
                if len(parts) > 1:
                    name_part = parts[1].split()[0]
                    title = f"Meeting with {name_part.title()}"

            tomorrow = datetime.now() + timedelta(days=1)
            tomorrow_3pm = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)

            return json.dumps({
                "calendar_events": [{
                    "title": title,
                    "start_time": tomorrow_3pm.isoformat(),
                    "end_time": (tomorrow_3pm + timedelta(hours=1)).isoformat(),
                    "description": "Demo meeting event",
                    "location": "Conference Room" if "conference" in prompt_lower else ""
                }],
                "todos": [],
                "contacts": [],
                "file_actions": [],
                "queries": [],
                "response": "📅 I've created a meeting event for you. This is a demo response - the meeting has been added to your local storage."
            })
        elif "remind" in prompt_lower or "todo" in prompt_lower:
            title = "Call the bank"
            if "call" in prompt_lower and "bank" in prompt_lower:
                title = "Call the bank"
            elif "remind me to" in prompt_lower:
                start = prompt_lower.find("remind me to") + 12
                title = prompt[start:].strip()

            due_date = datetime.now() + timedelta(days=5) # Next Tuesday
            due_date = due_date.replace(hour=9, minute=0, second=0, microsecond=0)

            return json.dumps({
                "calendar_events": [],
                "todos": [{
                    "title": title.title(),
                    "description": "Demo todo item",
                    "due_date": due_date.isoformat(),
                    "priority": "normal"
                }],
                "contacts": [],
                "file_actions": [],
                "queries": [],
                "response": "✅ I've added that as a todo item. This is a demo response - the task has been saved locally."
            })
        elif "contact" in prompt_lower and ("add" in prompt_lower or "create" in prompt_lower):
            name = "John Doe"
            email = ""
            phone = ""

            if "john doe" in prompt_lower:
                name = "John Doe"
            if "@" in prompt:
                email_start = prompt.lower().find("email")
                if email_start > -1:
                    email_part = prompt[email_start:].split()[1] if " " in prompt[email_start:] else ""
                    if "@" in email_part:
                        email = email_part.rstrip(",")
            if "phone" in prompt_lower:
                phone = "+1234567890"

            return json.dumps({
                "calendar_events": [],
                "todos": [],
                "contacts": [{
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "company": "Demo Company"
                }],
                "file_actions": [],
                "queries": [],
                "response": "📇 I've added the contact information. This is a demo response - the contact has been saved locally."
            })
        else:
            return json.dumps({
                "calendar_events": [],
                "todos": [],
                "contacts": [],
                "file_actions": [],
                "queries": [],
                "response": f"I understand you said: '{prompt}'. This is a demo response from the Enhanced Personal Assistant. In full mode, I would use AI to provide intelligent responses and actions."
            })

class FileMonitor(FileSystemEventHandler):
    """Monitor file system changes"""
    
    def __init__(self, assistant):
        self.assistant = assistant
        self.recent_activities = []
    
    def on_modified(self, event):
        if not event.is_directory:
            self.log_activity(event.src_path, "modified")
    
    def on_created(self, event):
        if not event.is_directory:
            self.log_activity(event.src_path, "created")
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.log_activity(event.src_path, "deleted")
    
    def log_activity(self, filepath: str, action: str):
        activity = FileActivity(
            filepath=filepath,
            action=action,
            timestamp=datetime.now(),
            description=f"File {action}: {Path(filepath).name}"
        )
        self.recent_activities.append(activity)
        
        # Keep only last 100 activities
        if len(self.recent_activities) > 100:
            self.recent_activities = self.recent_activities[-100:]
        
        logger.info(f"File activity: {activity.description}")

class EnhancedPersonalAssistant:
    def __init__(self, config_file: str = "enhanced_config.json", data_dir: str = "./data"):
        """Initialize enhanced personal assistant"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.config = self.load_config(config_file)
        self.llm_provider = self.setup_llm_provider()
        
        # Initialize storage
        self.events_file = self.data_dir / "events.json"
        self.todos_file = self.data_dir / "todos.json"
        self.contacts_file = self.data_dir / "contacts.json"
        self.activities_file = self.data_dir / "activities.json"
        
        # Load data
        self.events = self.load_events()
        self.todos = self.load_todos()
        self.contacts = self.load_contacts()
        self.file_activities = []
        
        # Initialize CalDAV/CardDAV
        self.caldav_client = None
        self.carddav_client = None
        self.calendars = {}
        self.address_books = {}
        
        # Setup connections
        self.connect_caldav()
        self.connect_carddav()
        self.discover_calendars()
        self.discover_address_books()
        
        # Setup file monitoring
        self.setup_file_monitoring()
        
        # Setup scheduled tasks
        self.setup_scheduled_tasks()
        
        logger.info("Enhanced Personal Assistant initialized")
    
    def load_config(self, config_file: str) -> Dict:
        """Load enhanced configuration"""
        default_config = {
            "llm": {
                "provider": "openai",  # openai, ollama, anthropic
                "model": "gpt-4",
                "api_key": "",
                "base_url": "",
                "max_tokens": 2000
            },
            "caldav": {
                "url": "",
                "username": "",
                "password": ""
            },
            "carddav": {
                "url": "",
                "username": "",
                "password": ""
            },
            "monitoring": {
                "watch_directories": ["~/Downloads", "~/Documents"],
                "file_extensions": [".pdf", ".doc", ".docx", ".txt", ".md"],
                "daily_summary_time": "18:00"
            },
            "preferences": {
                "default_calendar": "Personal",
                "default_event_duration": 60,
                "timezone": "UTC",
                "auto_categorize": True,
                "smart_suggestions": True
            },
            "integrations": {
                "email_enabled": False,
                "email_server": "",
                "web_interface": True,
                "api_enabled": True
            }
        }
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            # Merge with defaults
            self._deep_merge(default_config, config)
            return default_config
        except FileNotFoundError:
            logger.info(f"Config file {config_file} not found. Creating with defaults...")
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
        except Exception as e:
            logger.error(f"Failed to load config file {config_file}: {e.__class__.__name__}: {e}")
            raise
    
    def _deep_merge(self, default: Dict, user: Dict):
        """Deep merge user config into default config"""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._deep_merge(default[key], value)
            else:
                default[key] = value
    
    def setup_llm_provider(self) -> LLMProvider:
        """Setup LLM provider based on configuration"""
        llm_config = self.config["llm"]
        provider_name = llm_config["provider"].lower()
        
        if provider_name == "openai":
            return OpenAIProvider(llm_config)
        elif provider_name == "ollama":
            return OllamaProvider(llm_config)
        elif provider_name == "anthropic":
            return AnthropicProvider(llm_config)
        elif provider_name == "demo":
            return DemoProvider(llm_config)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
    
    def connect_caldav(self):
        """Connect to CalDAV server"""
        caldav_config = self.config["caldav"]
        if caldav_config["url"] and caldav_config["username"]:
            try:
                self.caldav_client = DAVClient(
                    url=caldav_config["url"],
                    username=caldav_config["username"],
                    password=caldav_config["password"]
                )
                logger.info("✓ Connected to CalDAV server")
            except caldav.lib.error.AuthorizationError:
                logger.warning("Could not connect to CalDAV: Invalid username or password.")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Could not connect to CalDAV: Network or connection error: {e}")
            except Exception as e:
                logger.warning(f"Could not connect to CalDAV: Unexpected error: {e.__class__.__name__}: {e}")
    
    def connect_carddav(self):
        """Connect to CardDAV server"""
        carddav_config = self.config["carddav"]
        if carddav_config["url"] and carddav_config["username"]:
            try:
                self.carddav_client = DAVClient(
                    url=carddav_config["url"],
                    username=carddav_config["username"],
                    password=carddav_config["password"]
                )
                logger.info("✓ Connected to CardDAV server")
            except caldav.lib.error.AuthorizationError:
                logger.warning("Could not connect to CardDAV: Invalid username or password.")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Could not connect to CardDAV: Network or connection error: {e}")
            except Exception as e:
                logger.warning(f"Could not connect to CardDAV: Unexpected error: {e.__class__.__name__}: {e}")
    
    def discover_calendars(self):
        """Discover available calendars"""
        if not self.caldav_client:
            return
        
        try:
            principal = self.caldav_client.principal()
            calendars = principal.calendars()
            
            for calendar in calendars:
                name = calendar.name or "Unnamed Calendar"
                self.calendars[name] = calendar
                logger.info(f"📅 Found calendar: {name}")
            except caldav.lib.error.NotFoundError:
                logger.error("Error discovering calendars: Principal or calendar collection not found.")
            except Exception as e:
                logger.error(f"Error discovering calendars: Unexpected error: {e.__class__.__name__}: {e}")
    
    def discover_address_books(self):
        """Discover available address books"""
        if not self.carddav_client:
            return
        
        try:
            principal = self.carddav_client.principal()
            address_books = principal.address_books()
            
            for ab in address_books:
                name = ab.name or "Unnamed Address Book"
                self.address_books[name] = ab
                logger.info(f"📇 Found address book: {name}")
            except caldav.lib.error.NotFoundError:
                logger.error("Error discovering address books: Principal or address book collection not found.")
            except Exception as e:
                logger.error(f"Error discovering address books: Unexpected error: {e.__class__.__name__}: {e}")
    
    def setup_file_monitoring(self):
        """Setup file system monitoring"""
        try:
            self.file_monitor = FileMonitor(self)
            self.observer = Observer()
            
            watch_dirs = self.config["monitoring"]["watch_directories"]
            for watch_dir in watch_dirs:
                expanded_dir = os.path.expanduser(watch_dir)
                if os.path.exists(expanded_dir):
                    self.observer.schedule(self.file_monitor, expanded_dir, recursive=True)
                    logger.info(f"👁️ Monitoring directory: {expanded_dir}")
            
            self.observer.start()
        except Exception as e:
            logger.error(f"Failed to setup file monitoring: {e}")
    
    def setup_scheduled_tasks(self):
        """Setup scheduled tasks"""
        try:
            # Daily summary
            summary_time = self.config["monitoring"]["daily_summary_time"]
            schedule.every().day.at(summary_time).do(self.generate_daily_summary)
            
            # Weekly cleanup
            schedule.every().sunday.at("23:00").do(self.cleanup_old_data)
            
            # Start scheduler in background
            def run_scheduler():
                while True:
                    schedule.run_pending()
                    time.sleep(60)
            
            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
            logger.info("⏰ Scheduled tasks initialized")
        except ValueError as e:
            logger.error(f"Failed to setup scheduled tasks: Invalid time format in configuration: {e}")
        except Exception as e:
            logger.error(f"Failed to setup scheduled tasks: Unexpected error: {e.__class__.__name__}: {e}")
    
    async def extract_information_with_llm(self, user_input: str) -> Dict:
        """Use LLM to extract comprehensive information from natural language"""
        
        current_time = datetime.now().isoformat()
        existing_contacts = [{"name": c.name, "email": c.email} for c in self.contacts[:5]]
        upcoming_events = [{"title": e.title, "time": e.start_time.isoformat()} for e in self.get_upcoming_events(3)]
        
        system_prompt = f"""You are an expert personal assistant AI that extracts and processes information from natural language.

Analyze the user's input and extract any calendar events, todo items, contacts, or other relevant information. Return a JSON object with this exact structure:

{{
  "calendar_events": [
    {{
      "title": "Meeting title",
      "start_time": "2024-01-15T14:30:00",
      "end_time": "2024-01-15T15:30:00",
      "description": "Event description",
      "location": "Location if mentioned",
      "attendees": ["email@example.com"],
      "recurring": false,
      "recurrence_rule": "FREQ=WEEKLY;BYDAY=MO" // if recurring
    }}
  ],
  "todos": [
    {{
      "title": "Task title",
      "description": "Task description",
      "due_date": "2024-01-15T09:00:00",
      "priority": "high",
      "tags": ["work", "urgent"]
    }}
  ],
  "contacts": [
    {{
      "name": "Person Name",
      "email": "email@example.com",
      "phone": "+1234567890",
      "company": "Company Name",
      "notes": "Additional context"
    }}
  ],
  "file_actions": [
    {{
      "action": "rename",
      "pattern": "screenshot*.png",
      "new_name": "project_screenshot_{{date}}.png",
      "description": "Rename screenshots with date"
    }}
  ],
  "queries": [
    {{
      "type": "search_events",
      "query": "meetings this week",
      "filters": {{"calendar": "work"}}
    }}
  ],
  "response": "Natural language response to the user"
}}

Context:
- Current date/time: {current_time}
- Recent contacts: {json.dumps(existing_contacts)}
- Upcoming events: {json.dumps(upcoming_events)}

Rules:
1. Extract ALL mentioned events, todos, contacts, and actions
2. Use ISO 8601 format for dates/times
3. Be intelligent about relative dates (today, tomorrow, next week, etc.)
4. Infer missing information (default times, durations, priorities)
5. Recognize recurring patterns (every Monday, weekly, monthly)
6. Extract file organization requests
7. Identify search queries or information requests
8. Generate helpful, contextual responses
9. ALWAYS return valid JSON only, no additional text
10. Be conservative - only extract what you're confident about"""
        
        try:
            llm_response = await self.llm_provider.generate_response(user_input, system_prompt)
            
            # Clean up and parse JSON
            json_str = llm_response.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:]
            if json_str.endswith('```'):
                json_str = json_str[:-3]
            
            result = json.loads(json_str)
            
            # Validate and set defaults
            for key in ["calendar_events", "todos", "contacts", "file_actions", "queries"]:
                if key not in result:
                    result[key] = []
            
            if "response" not in result:
                result["response"] = "I've processed your request."
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.error(f"Raw response: {llm_response}")
            return {
                "calendar_events": [],
                "todos": [],
                "contacts": [],
                "file_actions": [],
                "queries": [],
                "response": "I had trouble understanding that request. Could you rephrase it?"
            }
        except Exception as e:
            logger.error(f"Error in LLM processing: {e}")
            return {
                "calendar_events": [],
                "todos": [],
                "contacts": [],
                "file_actions": [],
                "queries": [],
                "response": "Sorry, I encountered an error processing your request."
            }
    
    def create_calendar_event(self, event_data: Dict) -> bool:
        """Create enhanced calendar event with recurring support"""
        try:
            # Parse dates
            start_time = dateutil.parser.parse(event_data['start_time'])
            end_time = dateutil.parser.parse(event_data['end_time']) if event_data.get('end_time') else start_time + timedelta(hours=1)
            
            event = CalendarEvent(
                title=event_data['title'],
                start_time=start_time,
                end_time=end_time,
                description=event_data.get('description', ''),
                location=event_data.get('location', ''),
                attendees=event_data.get('attendees', []),
                uid=str(uuid.uuid4()),
                recurring=event_data.get('recurring', False),
                recurrence_rule=event_data.get('recurrence_rule'),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Save locally
            self.events.append(event)
            self.save_events()
            
            # Sync to CalDAV if available
            if self.caldav_client and self.calendars:
                self.sync_event_to_caldav(event)
            
            logger.info(f"✓ Created event: {event.title} at {event.start_time.strftime('%Y-%m-%d %H:%M')}")
            return True
            
        except dateutil.parser._parser.ParserError as e:
            logger.error(f"Error parsing date for event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error creating event: {e.__class__.__name__}: {e}")
            return False
    
    def sync_event_to_caldav(self, event: CalendarEvent):
        """Sync event to CalDAV server"""
        try:
            calendar_name = self.config["preferences"]["default_calendar"]
            calendar = self.calendars.get(calendar_name) or list(self.calendars.values())[0]
            
            # Create iCalendar event
            cal = Calendar()
            cal.add('prodid', '-//Enhanced Personal Assistant//EN')
            cal.add('version', '2.0')
            
            ical_event = Event()
            ical_event.add('uid', event.uid)
            ical_event.add('dtstart', event.start_time)
            ical_event.add('dtend', event.end_time)
            ical_event.add('summary', event.title)
            ical_event.add('description', event.description)
            
            if event.location:
                ical_event.add('location', event.location)
            
            if event.recurring and event.recurrence_rule:
                ical_event.add('rrule', event.recurrence_rule)
            
            cal.add_component(ical_event)
            calendar.add_event(cal.to_ical().decode('utf-8'))
            
            except caldav.lib.error.NotFoundError:
                logger.error("Error syncing event to CalDAV: Target calendar not found.")
            except caldav.lib.error.ReportError as e:
                logger.error(f"Error syncing event to CalDAV: CalDAV report error: {e}")
            except Exception as e:
                logger.error(f"Error syncing event to CalDAV: Unexpected error: {e.__class__.__name__}: {e}")
    
    def create_todo(self, todo_data: Dict) -> bool:
        """Create enhanced todo item"""
        try:
            todo = TodoItem(
                title=todo_data['title'],
                description=todo_data.get('description', ''),
                due_date=dateutil.parser.parse(todo_data['due_date']) if todo_data.get('due_date') else None,
                priority=todo_data.get('priority', 'normal'),
                tags=todo_data.get('tags', []),
                uid=str(uuid.uuid4()),
                created_at=datetime.now()
            )
            
            self.todos.append(todo)
            self.save_todos()
            
            logger.info(f"✅ Created todo: {todo.title}")
            return True
            
        except dateutil.parser._parser.ParserError as e:
            logger.error(f"Error parsing date for todo: {e}")
            return False
        except Exception as e:
            logger.error(f"Error creating todo: {e.__class__.__name__}: {e}")
            return False
    
    def create_contact(self, contact_data: Dict) -> bool:
        """Create enhanced contact"""
        try:
            contact = Contact(
                name=contact_data['name'],
                phone=contact_data.get('phone'),
                email=contact_data.get('email'),
                company=contact_data.get('company'),
                notes=contact_data.get('notes', ''),
                uid=str(uuid.uuid4()),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.contacts.append(contact)
            self.save_contacts()
            
            # Sync to CardDAV if available
            if self.carddav_client and self.address_books:
                self.sync_contact_to_carddav(contact)
            
            logger.info(f"📇 Created contact: {contact.name}")
            return True
            
        except ValueError as e:
            logger.error(f"Error validating contact data: {e}")
            return False
        except Exception as e:
            logger.error(f"Error creating contact: {e.__class__.__name__}: {e}")
            return False
    
    def sync_contact_to_carddav(self, contact: Contact):
        """Sync contact to CardDAV server"""
        try:
            address_book = list(self.address_books.values())[0]
            
            # Create vCard
            vcard = vobject.vCard()
            vcard.add('fn')
            vcard.fn.value = contact.name
            
            vcard.add('n')
            name_parts = contact.name.split(' ', 1)
            vcard.n.value = vobject.vcard.Name(
                family=name_parts[-1] if len(name_parts) > 1 else '',
                given=name_parts[0]
            )
            
            if contact.email:
                vcard.add('email')
                vcard.email.value = contact.email
                vcard.email.type_param = ['INTERNET']
            
            if contact.phone:
                vcard.add('tel')
                vcard.tel.value = contact.phone
                vcard.tel.type_param = ['VOICE']
            
            if contact.company:
                vcard.add('org')
                vcard.org.value = [contact.company]
            
            if contact.notes:
                vcard.add('note')
                vcard.note.value = contact.notes
            
            address_book.add_contact(vcard.serialize())
            
            except caldav.lib.error.NotFoundError:
                logger.error("Error syncing contact to CardDAV: Target address book not found.")
            except caldav.lib.error.ReportError as e:
                logger.error(f"Error syncing contact to CardDAV: CardDAV report error: {e}")
            except Exception as e:
                logger.error(f"Error syncing contact to CardDAV: Unexpected error: {e.__class__.__name__}: {e}")
    
        def load_events(self) -> List[CalendarEvent]:
            """Load events from file"""
            try:
                with open(self.events_file, 'r') as f:
                    data = json.load(f)
                return [
                    CalendarEvent(
                        title=item['title'],
                        start_time=datetime.fromisoformat(item['start_time']),
                        end_time=datetime.fromisoformat(item['end_time']) if item.get('end_time') else None,
                        description=item.get('description', ''),
                        location=item.get('location', ''),
                        attendees=item.get('attendees', []),
                        uid=item.get('uid'),
                        recurring=item.get('recurring', False),
                        recurrence_rule=item.get('recurrence_rule'),
                        created_at=datetime.fromisoformat(item['created_at']) if item.get('created_at') else None,
                        updated_at=datetime.fromisoformat(item['updated_at']) if item.get('updated_at') else None
                    )
                    for item in data
                ]
            except FileNotFoundError:
                return []        except PermissionError:
            logger.error(f"Permission denied when trying to read {self.events_file}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {self.events_file}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error loading events from {self.events_file}: {e.__class__.__name__}: {e}")
            return []
    
    def save_events(self):
        """Save events to file"""
        data = [
            {
                'title': event.title,
                'start_time': event.start_time.isoformat(),
                'end_time': event.end_time.isoformat() if event.end_time else None,
                'description': event.description,
                'location': event.location,
                'attendees': event.attendees or [],
                'uid': event.uid,
                'recurring': event.recurring,
                'recurrence_rule': event.recurrence_rule,
                'created_at': event.created_at.isoformat() if event.created_at else None,
                'updated_at': event.updated_at.isoformat() if event.updated_at else None
            }
            for event in self.events
        ]
        try:
            with open(self.events_file, 'w') as f:
                json.dump(data, f, indent=2)
        except PermissionError:
            logger.error(f"Permission denied when trying to write to {self.events_file}")
        except IOError as e:
            logger.error(f"I/O error when writing to {self.events_file}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving events to {self.events_file}: {e.__class__.__name__}: {e}")
    
    def load_todos(self) -> List[TodoItem]:
        """Load todos from file"""
        try:
            with open(self.todos_file, 'r') as f:
                data = json.load(f)
            return [
                TodoItem(
                    title=item['title'],
                    description=item.get('description', ''),
                    due_date=datetime.fromisoformat(item['due_date']) if item.get('due_date') else None,
                    priority=item.get('priority', 'normal'),
                    completed=item.get('completed', False),
                    uid=item.get('uid'),
                    tags=item.get('tags', []),
                    created_at=datetime.fromisoformat(item['created_at']) if item.get('created_at') else None,
                    completed_at=datetime.fromisoformat(item['completed_at']) if item.get('completed_at') else None
                )
                for item in data
            ]
        except FileNotFoundError:
            return []
        except PermissionError:
            logger.error(f"Permission denied when trying to read {self.todos_file}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {self.todos_file}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error loading todos from {self.todos_file}: {e.__class__.__name__}: {e}")
            return []
    
    def save_todos(self):
        """Save todos to file"""
        data = [
            {
                'title': todo.title,
                'description': todo.description,
                'due_date': todo.due_date.isoformat() if todo.due_date else None,
                'priority': todo.priority,
                'completed': todo.completed,
                'uid': todo.uid,
                'tags': todo.tags or [],
                'created_at': todo.created_at.isoformat() if todo.created_at else None,
                'completed_at': todo.completed_at.isoformat() if todo.completed_at else None
            }
            for todo in self.todos
        ]
        try:
            with open(self.todos_file, 'w') as f:
                json.dump(data, f, indent=2)
        except PermissionError:
            logger.error(f"Permission denied when trying to write to {self.todos_file}")
        except IOError as e:
            logger.error(f"I/O error when writing to {self.todos_file}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving todos to {self.todos_file}: {e.__class__.__name__}: {e}")
    
    def load_contacts(self) -> List[Contact]:
        """Load contacts from file"""
        try:
            with open(self.contacts_file, 'r') as f:
                data = json.load(f)
            return [
                Contact(
                    name=item['name'],
                    phone=item.get('phone'),
                    email=item.get('email'),
                    company=item.get('company'),
                    notes=item.get('notes', ''),
                    uid=item.get('uid'),
                    created_at=datetime.fromisoformat(item['created_at']) if item.get('created_at') else None,
                    updated_at=datetime.fromisoformat(item['updated_at']) if item.get('updated_at') else None
                )
                for item in data
            ]
        except FileNotFoundError:
            return []
        except PermissionError:
            logger.error(f"Permission denied when trying to read {self.contacts_file}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {self.contacts_file}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error loading contacts from {self.contacts_file}: {e.__class__.__name__}: {e}")
            return []
    
    def save_contacts(self):
        """Save contacts to file"""
        data = [
            {
                'name': contact.name,
                'phone': contact.phone,
                'email': contact.email,
                'company': contact.company,
                'notes': contact.notes,
                'uid': contact.uid,
                'created_at': contact.created_at.isoformat() if contact.created_at else None,
                'updated_at': contact.updated_at.isoformat() if contact.updated_at else None
            }
            for contact in self.contacts
        ]
        try:
            with open(self.contacts_file, 'w') as f:
                json.dump(data, f, indent=2)
        except PermissionError:
            logger.error(f"Permission denied when trying to write to {self.contacts_file}")
        except IOError as e:
            logger.error(f"I/O error when writing to {self.contacts_file}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving contacts to {self.contacts_file}: {e.__class__.__name__}: {e}")
    
    def get_upcoming_events(self, days: int = 7) -> List[CalendarEvent]:
        """Get upcoming events"""
        now = datetime.now()
        end_date = now + timedelta(days=days)
        
        upcoming = [
            event for event in self.events
            if event.start_time >= now and event.start_time <= end_date
        ]
        
        return sorted(upcoming, key=lambda x: x.start_time)
    
    def get_pending_todos(self) -> List[TodoItem]:
        """Get pending todos sorted by priority and due date"""
        pending = [todo for todo in self.todos if not todo.completed]
        
        # Sort by priority (high -> normal -> low) then by due date
        priority_order = {'high': 0, 'normal': 1, 'low': 2}
        return sorted(pending, key=lambda x: (
            priority_order.get(x.priority, 1),
            x.due_date or datetime.max
        ))
    
    def search_contacts(self, query: str) -> List[Contact]:
        """Enhanced contact search"""
        query = query.lower()
        results = []
        
        for contact in self.contacts:
            score = 0
            if query in contact.name.lower():
                score += 10
            if contact.email and query in contact.email.lower():
                score += 8
            if contact.phone and query in contact.phone:
                score += 6
            if contact.company and query in contact.company.lower():
                score += 4
            if contact.notes and query in contact.notes.lower():
                score += 2
            
            if score > 0:
                results.append((contact, score))
        
        # Sort by relevance score
        return [contact for contact, score in sorted(results, key=lambda x: x[1], reverse=True)]
    
    async def generate_daily_summary(self):
        """Generate AI-powered daily summary"""
        try:
            today = datetime.now().date()
            
            # Gather data for today
            todays_events = [e for e in self.events if e.start_time.date() == today]
            todays_todos = [t for t in self.todos if t.created_at and t.created_at.date() == today]
            recent_activities = self.file_monitor.recent_activities[-20:] if hasattr(self, 'file_monitor') else []
            
            # Create summary prompt
            summary_data = {
                "date": today.isoformat(),
                "events": [{"title": e.title, "time": e.start_time.isoformat()} for e in todays_events],
                "todos_created": [{"title": t.title, "priority": t.priority} for t in todays_todos],
                "file_activities": [{"file": a.filepath, "action": a.action} for a in recent_activities]
            }
            
            prompt = f"""Generate a concise daily summary for {today}. Here's what happened:

{json.dumps(summary_data, indent=2)}

Create a brief, friendly summary highlighting:
1. Key events and meetings
2. Tasks created or completed
3. Notable file activities
4. Overall productivity insights

Keep it under 200 words and make it actionable."""
            
            summary = await self.llm_provider.generate_response(prompt)
            
            # Save summary
            summary_file = self.data_dir / f"daily_summary_{today}.txt"
            with open(summary_file, 'w') as f:
                f.write(f"Daily Summary - {today}\n")
                f.write("=" * 40 + "\n\n")
                f.write(summary)
            
            logger.info(f"📊 Generated daily summary for {today}")
            return summary
            
            except PermissionError:
                logger.error(f"Permission denied when trying to write daily summary to {summary_file}")
                return None
            except IOError as e:
                logger.error(f"I/O error when writing daily summary to {summary_file}: {e}")
                return None
            except Exception as e:
                logger.error(f"Error generating daily summary: {e.__class__.__name__}: {e}")
                return None
    
    def cleanup_old_data(self):
        """Clean up old data"""
        try:
            # Remove completed todos older than 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            original_count = len(self.todos)
            
            self.todos = [
                todo for todo in self.todos
                if not todo.completed or 
                (todo.completed_at and todo.completed_at > cutoff_date)
            ]
            
            removed_count = original_count - len(self.todos)
            if removed_count > 0:
                self.save_todos()
                logger.info(f"🧹 Cleaned up {removed_count} old completed todos")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_input(self, user_input: str) -> str:
        """Enhanced input processing with LLM"""
        try:
            # Handle special commands
            if user_input.lower().startswith('/'):
                return await self.handle_command(user_input)
            
            # Extract information using LLM
            result = await self.extract_information_with_llm(user_input)
            
            # Process calendar events
            for event_data in result.get("calendar_events", []):
                self.create_calendar_event(event_data)
            
            # Process todos
            for todo_data in result.get("todos", []):
                self.create_todo(todo_data)
            
            # Process contacts
            for contact_data in result.get("contacts", []):
                self.create_contact(contact_data)
            
            # Process file actions
            for action in result.get("file_actions", []):
                await self.handle_file_action(action)
            
            # Process queries
            for query in result.get("queries", []):
                query_result = await self.handle_query(query)
                if query_result:
                    result["response"] += f"\n\n{query_result}"
            
            return result.get("response", "I've processed your request.")
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return "Sorry, I encountered an error processing your request."
    
    async def handle_file_action(self, action: Dict):
        """Handle file organization actions"""
        # This would implement file renaming, organizing, etc.
        # For now, just log the action
        logger.info(f"File action requested: {action}")
    
    async def handle_query(self, query: Dict) -> Optional[str]:
        """Handle information queries"""
        query_type = query.get("type")
        
        if query_type == "search_events":
            events = self.get_upcoming_events(14)  # 2 weeks
            if events:
                result = "📅 Upcoming events:\n"
                for event in events[:5]:
                    result += f"• {event.title} - {event.start_time.strftime('%m/%d %H:%M')}\n"
                return result
            else:
                return "No upcoming events found."
        
        elif query_type == "search_todos":
            todos = self.get_pending_todos()
            if todos:
                result = "✅ Pending todos:\n"
                for todo in todos[:5]:
                    result += f"• {todo.title} ({todo.priority})\n"
                return result
            else:
                return "No pending todos found."
        
        return None
    
    async def handle_command(self, command: str) -> str:
        """Handle enhanced commands"""
        command = command.lower().strip()
        
        if command == '/upcoming':
            events = self.get_upcoming_events()
            if not events:
                return "📅 No upcoming events found."
            
            response = "📅 Upcoming events:\n"
            for event in events[:10]:
                response += f"• {event.title} - {event.start_time.strftime('%m/%d %H:%M')}"
                if event.location:
                    response += f" @ {event.location}"
                if event.recurring:
                    response += " (recurring)"
                response += "\n"
            return response
        
        elif command == '/todos':
            todos = self.get_pending_todos()
            if not todos:
                return "✅ No pending todos!"
            
            response = "✅ Pending todos:\n"
            for todo in todos[:10]:
                response += f"• {todo.title}"
                if todo.due_date:
                    response += f" - Due: {todo.due_date.strftime('%m/%d %H:%M')}"
                response += f" ({todo.priority})"
                if todo.tags:
                    response += f" [{', '.join(todo.tags)}]"
                response += "\n"
            return response
        
        elif command.startswith('/search '):
            query = command[8:]
            contacts = self.search_contacts(query)
            if not contacts:
                return f"📇 No contacts found for '{query}'"
            
            response = f"📇 Found {len(contacts)} contact(s):\n"
            for contact in contacts[:5]:
                response += f"• {contact.name}"
                if contact.email:
                    response += f" - {contact.email}"
                if contact.phone:
                    response += f" - {contact.phone}"
                if contact.company:
                    response += f" ({contact.company})"
                response += "\n"
            return response
        
        elif command == '/summary':
            summary = await self.generate_daily_summary()
            return summary or "Could not generate summary."
        
        elif command == '/stats':
            total_events = len(self.events)
            pending_todos = len(self.get_pending_todos())
            total_contacts = len(self.contacts)
            
            return f"""📊 Assistant Statistics:
• Events: {total_events}
• Pending Todos: {pending_todos}
• Contacts: {total_contacts}
• Data Directory: {self.data_dir}
• LLM Provider: {self.config['llm']['provider']}
• CalDAV: {'✓' if self.caldav_client else '✗'}
• CardDAV: {'✓' if self.carddav_client else '✗'}"""
        
        elif command == '/help':
            return """🤖 Enhanced Personal Assistant Commands:

**Data Management:**
/upcoming - Show upcoming events
/todos - Show pending todos
/search <query> - Search contacts
/summary - Generate daily summary
/stats - Show statistics

**Natural Language Examples:**
• "Meeting with John tomorrow at 3pm in conference room"
• "Remind me to call Sarah next Tuesday, high priority"
• "Add Jane Doe to contacts, email jane@company.com, works at TechCorp"
• "Weekly standup every Monday at 9am"
• "Show me meetings this week"

**Advanced Features:**
• Recurring events support
• File monitoring and organization
• Daily summaries with AI insights
• Multi-provider LLM support
• CalDAV/CardDAV sync
• Smart contact search
• Priority-based todo management
"""
        
        else:
            return "❓ Unknown command. Type /help for available commands."

async def main():
    """Main async interface"""
    print("🤖 Enhanced Personal Assistant (organizer-pipeline)")
    print("=" * 60)
    print("Initializing advanced features...")
    
    try:
        assistant = EnhancedPersonalAssistant()
    except Exception as e:
        logger.error(f"Failed to initialize assistant: {e.__class__.__name__}: {e}")
        print(f"❌ Failed to initialize assistant: {e}")
        print("\nPlease check your configuration and dependencies.")
        return

    print("\n✓ Enhanced Assistant ready!")
    print("🧠 LLM-powered natural language processing")
    print("📊 File monitoring and daily summaries")
    print("🔄 CalDAV/CardDAV sync capabilities")
    print("\nType /help for commands or just talk naturally")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                # Cleanup
                if hasattr(assistant, 'observer'):
                    assistant.observer.stop()
                    assistant.observer.join()
                break
            
            if not user_input:
                continue
            
            response = await assistant.process_input(user_input)
            print(f"Assistant: {response}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            if hasattr(assistant, 'observer'):
                assistant.observer.stop()
                assistant.observer.join()
            break
        except EOFError:
            print("\n👋 Goodbye!")
            if hasattr(assistant, 'observer'):
                assistant.observer.stop()
                assistant.observer.join()
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
