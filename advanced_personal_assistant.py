#!/usr/bin/env python3
"""
Advanced Local LLM Personal Assistant
Full CalDAV/CardDAV integration with real LLM processing
"""

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import caldav
from caldav import DAVClient
import vobject
import openai
import requests
from urllib.parse import urljoin
import os
from pathlib import Path
import icalendar
from icalendar import Calendar, Event, Todo, vText
import dateutil.parser

@dataclass
class Contact:
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    notes: str = ""
    uid: Optional[str] = None

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

@dataclass
class TodoItem:
    title: str
    description: str = ""
    due_date: Optional[datetime] = None
    priority: str = "normal"
    completed: bool = False
    uid: Optional[str] = None

class AdvancedPersonalAssistant:
    def __init__(self, config_file: str = "assistant_config.json"):
        """Initialize with configuration"""
        self.config = self.load_config(config_file)
        self.caldav_client = None
        self.carddav_client = None
        self.calendars = {}
        self.address_books = {}
        
        # Initialize LLM client
        self.setup_llm()
        
        # Connect to CalDAV/CardDAV servers
        self.connect_caldav()
        self.connect_carddav()
        
        # Load calendars and address books
        self.discover_calendars()
        self.discover_address_books()
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from file"""
        default_config = {
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
            "llm": {
                "provider": "openai",  # or "ollama", "anthropic"
                "model": "gpt-4",
                "api_key": "",
                "base_url": "https://api.openai.com/v1"
            },
            "preferences": {
                "default_calendar": "Personal",
                "default_event_duration": 60,  # minutes
                "timezone": "UTC"
            }
        }
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            # Merge with defaults
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
            return config
        except FileNotFoundError:
            print(f"Config file {config_file} not found. Creating with defaults...")
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def setup_llm(self):
        """Setup LLM client based on configuration"""
        llm_config = self.config["llm"]
        
        if llm_config["provider"] == "openai":
            openai.api_key = llm_config["api_key"]
            self.llm_client = openai
        elif llm_config["provider"] == "ollama":
            # Setup for local Ollama
            self.llm_base_url = llm_config.get("base_url", "http://localhost:11434")
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_config['provider']}")
    
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
                print("✓ Connected to CalDAV server")
            except Exception as e:
                print(f"⚠ Could not connect to CalDAV: {e}")
    
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
                print("✓ Connected to CardDAV server")
            except Exception as e:
                print(f"⚠ Could not connect to CardDAV: {e}")
    
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
                print(f"📅 Found calendar: {name}")
        except Exception as e:
            print(f"Error discovering calendars: {e}")
    
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
                print(f"📇 Found address book: {name}")
        except Exception as e:
            print(f"Error discovering address books: {e}")
    
    def call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Call LLM with given prompt"""
        llm_config = self.config["llm"]
        
        try:
            if llm_config["provider"] == "openai":
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = self.llm_client.chat.completions.create(
                    model=llm_config["model"],
                    messages=messages,
                    temperature=0.3
                )
                return response.choices[0].message.content
            
            elif llm_config["provider"] == "ollama":
                # Call local Ollama
                response = requests.post(
                    f"{self.llm_base_url}/api/generate",
                    json={
                        "model": llm_config["model"],
                        "prompt": f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:",
                        "stream": False
                    }
                )
                return response.json()["response"]
        
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return "Sorry, I couldn't process that request."
    
    def extract_calendar_events_and_todos(self, user_input: str) -> Dict:
        """Use LLM to extract calendar events and todos from natural language"""
        
        current_time = datetime.now().isoformat()
        
        system_prompt = f"""You are an expert at extracting calendar events and todo items from natural language. 

Analyze the user's input and extract any calendar events or todo items mentioned. Return a JSON object with this exact structure:

{{
  "calendar_events": [
    {{
      "title": "Meeting title",
      "start_time": "2024-01-15T14:30:00",
      "end_time": "2024-01-15T15:30:00",
      "description": "Event description",
      "location": "Location if mentioned",
      "attendees": ["email@example.com"]
    }}
  ],
  "todos": [
    {{
      "title": "Task title",
      "description": "Task description",
      "due_date": "2024-01-15T09:00:00",
      "priority": "high"
    }}
  ],
  "contacts": [
    {{
      "name": "Person Name",
      "email": "email@example.com",
      "phone": "+1234567890",
      "company": "Company Name"
    }}
  ],
  "response": "Natural language response to the user"
}}

Rules:
- Extract ALL calendar events mentioned (meetings, appointments, etc.)
- Extract ALL todo items (tasks, reminders, things to do)
- Extract ALL contact information mentioned
- Use ISO 8601 format for dates/times
- If no time specified, use 9:00 AM for todos, current time + 1 hour for events
- If no end time specified for events, add 1 hour to start time
- Be intelligent about relative dates (today, tomorrow, next week, etc.)
- Current date/time context: {current_time}
- ALWAYS return valid JSON only, no additional text"""
        
        llm_response = self.call_llm(user_input, system_prompt)
        
        try:
            # Clean up response and parse JSON
            json_str = llm_response.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:]
            if json_str.endswith('```'):
                json_str = json_str[:-3]
            
            result = json.loads(json_str)
            
            # Validate structure
            if "calendar_events" not in result:
                result["calendar_events"] = []
            if "todos" not in result:
                result["todos"] = []
            if "contacts" not in result:
                result["contacts"] = []
            if "response" not in result:
                result["response"] = "I've processed your request."
                
            return result
            
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {llm_response}")
            return {
                "calendar_events": [],
                "todos": [],
                "contacts": [],
                "response": "I had trouble understanding that request. Could you rephrase it?"
            }
    
    def create_calendar_event(self, event_data: Dict) -> bool:
        """Create a calendar event"""
        try:
            # Get the default calendar or first available
            calendar_name = self.config["preferences"]["default_calendar"]
            calendar = self.calendars.get(calendar_name) or list(self.calendars.values())[0]
            
            # Create iCalendar event
            cal = Calendar()
            cal.add('prodid', '-//Personal Assistant//EN')
            cal.add('version', '2.0')
            
            event = Event()
            event.add('uid', str(uuid.uuid4()))
            event.add('dtstart', dateutil.parser.parse(event_data['start_time']))
            
            if event_data.get('end_time'):
                event.add('dtend', dateutil.parser.parse(event_data['end_time']))
            else:
                # Default 1 hour duration
                start_time = dateutil.parser.parse(event_data['start_time'])
                event.add('dtend', start_time + timedelta(hours=1))
            
            event.add('summary', event_data['title'])
            event.add('description', event_data.get('description', ''))
            
            if event_data.get('location'):
                event.add('location', event_data['location'])
            
            cal.add_component(event)
            
            # Save to calendar
            calendar.add_event(cal.to_ical().decode('utf-8'))
            print(f"✓ Created event: {event_data['title']}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating event: {e}")
            return False
    
    def create_todo(self, todo_data: Dict) -> bool:
        """Create a todo item"""
        try:
            # Use first available calendar for todos
            calendar = list(self.calendars.values())[0]
            
            # Create iCalendar todo
            cal = Calendar()
            cal.add('prodid', '-//Personal Assistant//EN')
            cal.add('version', '2.0')
            
            todo = Todo()
            todo.add('uid', str(uuid.uuid4()))
            todo.add('summary', todo_data['title'])
            todo.add('description', todo_data.get('description', ''))
            
            if todo_data.get('due_date'):
                todo.add('due', dateutil.parser.parse(todo_data['due_date']))
            
            # Set priority
            priority_map = {'high': 1, 'normal': 5, 'low': 9}
            priority = priority_map.get(todo_data.get('priority', 'normal'), 5)
            todo.add('priority', priority)
            
            cal.add_component(todo)
            
            # Save to calendar
            calendar.add_todo(cal.to_ical().decode('utf-8'))
            print(f"✓ Created todo: {todo_data['title']}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating todo: {e}")
            return False
    
    def create_contact(self, contact_data: Dict) -> bool:
        """Create a contact"""
        if not self.address_books:
            print("📇 No address books available, saving contact locally")
            return self.save_contact_locally(contact_data)
        
        try:
            # Use first available address book
            address_book = list(self.address_books.values())[0]
            
            # Create vCard
            vcard = vobject.vCard()
            vcard.add('fn')
            vcard.fn.value = contact_data['name']
            
            vcard.add('n')
            name_parts = contact_data['name'].split(' ', 1)
            vcard.n.value = vobject.vcard.Name(
                family=name_parts[-1] if len(name_parts) > 1 else '',
                given=name_parts[0]
            )
            
            if contact_data.get('email'):
                vcard.add('email')
                vcard.email.value = contact_data['email']
                vcard.email.type_param = ['INTERNET']
            
            if contact_data.get('phone'):
                vcard.add('tel')
                vcard.tel.value = contact_data['phone']
                vcard.tel.type_param = ['VOICE']
            
            if contact_data.get('company'):
                vcard.add('org')
                vcard.org.value = [contact_data['company']]
            
            # Save to address book
            address_book.add_contact(vcard.serialize())
            print(f"✓ Created contact: {contact_data['name']}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating contact: {e}")
            return self.save_contact_locally(contact_data)
    
    def save_contact_locally(self, contact_data: Dict) -> bool:
        """Save contact to local file as fallback"""
        try:
            contacts_file = "local_contacts.json"
            contacts = []
            
            if os.path.exists(contacts_file):
                with open(contacts_file, 'r') as f:
                    contacts = json.load(f)
            
            contact_data['uid'] = str(uuid.uuid4())
            contacts.append(contact_data)
            
            with open(contacts_file, 'w') as f:
                json.dump(contacts, f, indent=2)
            
            print(f"✓ Saved contact locally: {contact_data['name']}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving contact locally: {e}")
            return False
    
    def get_upcoming_events(self, days: int = 7) -> List[Dict]:
        """Get upcoming events from all calendars"""
        events = []
        
        if not self.calendars:
            return events
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        
        for calendar_name, calendar in self.calendars.items():
            try:
                cal_events = calendar.date_search(start=start_date, end=end_date)
                
                for event in cal_events:
                    try:
                        # Parse the event data
                        ical = Calendar.from_ical(event.data)
                        for component in ical.walk():
                            if component.name == "VEVENT":
                                events.append({
                                    'title': str(component.get('summary', 'Untitled')),
                                    'start': component.get('dtstart').dt,
                                    'end': component.get('dtend').dt if component.get('dtend') else None,
                                    'description': str(component.get('description', '')),
                                    'location': str(component.get('location', '')),
                                    'calendar': calendar_name
                                })
                    except Exception as e:
                        print(f"Error parsing event: {e}")
            except Exception as e:
                print(f"Error getting events from {calendar_name}: {e}")
        
        return sorted(events, key=lambda x: x['start'])
    
    def search_contacts(self, query: str) -> List[Dict]:
        """Search contacts by name, email, or phone"""
        contacts = []
        
        # Search CardDAV address books
        for ab_name, address_book in self.address_books.items():
            try:
                for contact in address_book.search(query):
                    vcard = vobject.readOne(contact.data)
                    contacts.append({
                        'name': str(vcard.fn.value),
                        'email': str(vcard.email.value) if hasattr(vcard, 'email') else '',
                        'phone': str(vcard.tel.value) if hasattr(vcard, 'tel') else '',
                        'source': ab_name
                    })
            except Exception as e:
                print(f"Error searching {ab_name}: {e}")
        
        # Search local contacts
        try:
            if os.path.exists("local_contacts.json"):
                with open("local_contacts.json", 'r') as f:
                    local_contacts = json.load(f)
                
                for contact in local_contacts:
                    if (query.lower() in contact['name'].lower() or
                        query.lower() in contact.get('email', '').lower() or
                        query.lower() in contact.get('phone', '').lower()):
                        contact['source'] = 'local'
                        contacts.append(contact)
        except Exception as e:
            print(f"Error searching local contacts: {e}")
        
        return contacts
    
    def process_input(self, user_input: str) -> str:
        """Main processing function"""
        # Handle special commands
        if user_input.lower().startswith('/'):
            return self.handle_command(user_input)
        
        # Extract events, todos, and contacts using LLM
        result = self.extract_calendar_events_and_todos(user_input)
        
        # Process calendar events
        for event_data in result.get("calendar_events", []):
            self.create_calendar_event(event_data)
        
        # Process todos
        for todo_data in result.get("todos", []):
            self.create_todo(todo_data)
        
        # Process contacts
        for contact_data in result.get("contacts", []):
            self.create_contact(contact_data)
        
        return result.get("response", "I've processed your request.")
    
    def handle_command(self, command: str) -> str:
        """Handle special commands"""
        command = command.lower().strip()
        
        if command == '/upcoming':
            events = self.get_upcoming_events()
            if not events:
                return "📅 No upcoming events found."
            
            response = "📅 Upcoming events:\n"
            for event in events[:10]:  # Show first 10
                start_time = event['start'].strftime('%m/%d %H:%M')
                response += f"• {event['title']} - {start_time}"
                if event['location']:
                    response += f" @ {event['location']}"
                response += f" ({event['calendar']})\n"
            return response
        
        elif command.startswith('/search '):
            query = command[8:]  # Remove '/search '
            contacts = self.search_contacts(query)
            if not contacts:
                return f"📇 No contacts found for '{query}'"
            
            response = f"📇 Found {len(contacts)} contact(s):\n"
            for contact in contacts[:5]:  # Show first 5
                response += f"• {contact['name']}"
                if contact.get('email'):
                    response += f" - {contact['email']}"
                if contact.get('phone'):
                    response += f" - {contact['phone']}"
                response += f" ({contact['source']})\n"
            return response
        
        elif command == '/calendars':
            if not self.calendars:
                return "📅 No calendars available"
            response = "📅 Available calendars:\n"
            for name in self.calendars.keys():
                response += f"• {name}\n"
            return response
        
        elif command == '/help':
            return """🤖 Available commands:
/upcoming - Show upcoming events
/search <query> - Search contacts
/calendars - List available calendars
/help - Show this help

Natural language examples:
• "Meeting with John tomorrow at 3pm"
• "Remind me to call Sarah next week"
• "Add John Doe to contacts, email john@example.com"
• "I have a dentist appointment Friday at 10am"
"""
        
        else:
            return "❓ Unknown command. Type /help for available commands."

def main():
    """Main conversation interface"""
    print("🤖 Advanced Personal Assistant")
    print("=" * 50)
    print("Initializing...")
    
    try:
        assistant = AdvancedPersonalAssistant()
        print("\n✓ Assistant ready!")
        print("Type /help for commands or just talk naturally")
        print("Type 'quit' to exit\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                response = assistant.process_input(user_input)
                print(f"Assistant: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Failed to initialize assistant: {e}")
        print("\nPlease check your configuration and dependencies.")

if __name__ == "__main__":
    main()
