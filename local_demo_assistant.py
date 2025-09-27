#!/usr/bin/env python3
"""
Local Demo Personal Assistant
Test version without CalDAV/CardDAV requirements
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import os
import dateutil.parser

@dataclass
class CalendarEvent:
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    description: str = ""
    location: str = ""
    uid: Optional[str] = None

@dataclass
class TodoItem:
    title: str
    description: str = ""
    due_date: Optional[datetime] = None
    priority: str = "normal"
    completed: bool = False
    uid: Optional[str] = None

@dataclass
class Contact:
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    uid: Optional[str] = None

class LocalPersonalAssistant:
    def __init__(self):
        """Initialize local demo assistant"""
        self.events_file = "local_events.json"
        self.todos_file = "local_todos.json"
        self.contacts_file = "local_contacts.json"
        
        self.events = self.load_events()
        self.todos = self.load_todos()
        self.contacts = self.load_contacts()
        
        print("🤖 Local Demo Assistant initialized")
        print("✓ This version saves everything locally")
        print("✓ No CalDAV/CardDAV or LLM API required")
    
    def load_events(self) -> List[CalendarEvent]:
        """Load events from local file"""
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
                    uid=item.get('uid')
                )
                for item in data
            ]
        except FileNotFoundError:
            return []
    
    def save_events(self):
        """Save events to local file"""
        data = [
            {
                'title': event.title,
                'start_time': event.start_time.isoformat(),
                'end_time': event.end_time.isoformat() if event.end_time else None,
                'description': event.description,
                'location': event.location,
                'uid': event.uid
            }
            for event in self.events
        ]
        with open(self.events_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_todos(self) -> List[TodoItem]:
        """Load todos from local file"""
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
                    uid=item.get('uid')
                )
                for item in data
            ]
        except FileNotFoundError:
            return []
    
    def save_todos(self):
        """Save todos to local file"""
        data = [
            {
                'title': todo.title,
                'description': todo.description,
                'due_date': todo.due_date.isoformat() if todo.due_date else None,
                'priority': todo.priority,
                'completed': todo.completed,
                'uid': todo.uid
            }
            for todo in self.todos
        ]
        with open(self.todos_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_contacts(self) -> List[Contact]:
        """Load contacts from local file"""
        try:
            with open(self.contacts_file, 'r') as f:
                data = json.load(f)
            return [
                Contact(
                    name=item['name'],
                    phone=item.get('phone'),
                    email=item.get('email'),
                    company=item.get('company'),
                    uid=item.get('uid')
                )
                for item in data
            ]
        except FileNotFoundError:
            return []
    
    def save_contacts(self):
        """Save contacts to local file"""
        data = [
            {
                'name': contact.name,
                'phone': contact.phone,
                'email': contact.email,
                'company': contact.company,
                'uid': contact.uid
            }
            for contact in self.contacts
        ]
        with open(self.contacts_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def simple_parse_input(self, text: str) -> Dict:
        """Simple pattern-based parsing (demo purposes)"""
        text = text.lower()
        result = {
            "calendar_events": [],
            "todos": [],
            "contacts": [],
            "response": ""
        }
        
        # Simple calendar event detection
        if any(word in text for word in ['meeting', 'appointment', 'event', 'lunch', 'dinner']):
            # Extract basic info
            title = self.extract_title(text)
            start_time = self.extract_datetime(text)
            location = self.extract_location(text)
            
            result["calendar_events"].append({
                "title": title,
                "start_time": start_time.isoformat(),
                "end_time": (start_time + timedelta(hours=1)).isoformat(),
                "description": f"Created from: {text}",
                "location": location
            })
        
        # Simple todo detection
        if any(word in text for word in ['remind', 'todo', 'task', 'call', 'email', 'buy', 'don\'t forget']):
            title = self.extract_todo_title(text)
            due_date = self.extract_datetime(text)
            
            result["todos"].append({
                "title": title,
                "description": f"From: {text}",
                "due_date": due_date.isoformat() if due_date else None,
                "priority": "normal"
            })
        
        # Simple contact detection
        if any(word in text for word in ['contact', 'add', 'phone', 'email']):
            contact_info = self.extract_contact_info(text)
            if contact_info:
                result["contacts"].append(contact_info)
        
        # Generate response
        if result["calendar_events"]:
            result["response"] = f"📅 Created {len(result['calendar_events'])} event(s)"
        if result["todos"]:
            if result["response"]:
                result["response"] += " and "
            result["response"] += f"✅ Added {len(result['todos'])} todo(s)"
        if result["contacts"]:
            if result["response"]:
                result["response"] += " and "
            result["response"] += f"📇 Added {len(result['contacts'])} contact(s)"
        
        if not result["response"]:
            result["response"] = "I didn't detect any specific actions. Try phrases like 'meeting tomorrow at 3pm' or 'remind me to call John'."
        
        return result
    
    def extract_title(self, text: str) -> str:
        """Extract event title from text"""
        # Simple heuristics
        words = text.split()
        for i, word in enumerate(words):
            if word in ['meeting', 'appointment', 'lunch', 'dinner']:
                # Take words around it
                start = max(0, i-2)
                end = min(len(words), i+3)
                return ' '.join(words[start:end]).title()
        return "Event"
    
    def extract_todo_title(self, text: str) -> str:
        """Extract todo title from text"""
        # Remove common prefixes
        text = text.replace('remind me to ', '')
        text = text.replace('don\'t forget to ', '')
        text = text.replace('i need to ', '')
        
        # Take first few meaningful words
        words = text.split()[:5]
        return ' '.join(words).title()
    
    def extract_datetime(self, text: str) -> Optional[datetime]:
        """Extract datetime from text"""
        now = datetime.now()
        
        if 'today' in text:
            time = self.extract_time(text)
            return now.replace(hour=time.hour, minute=time.minute, second=0, microsecond=0)
        elif 'tomorrow' in text:
            time = self.extract_time(text)
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(hour=time.hour, minute=time.minute, second=0, microsecond=0)
        elif 'monday' in text:
            return self.next_weekday(now, 0, self.extract_time(text))
        elif 'tuesday' in text:
            return self.next_weekday(now, 1, self.extract_time(text))
        elif 'wednesday' in text:
            return self.next_weekday(now, 2, self.extract_time(text))
        elif 'thursday' in text:
            return self.next_weekday(now, 3, self.extract_time(text))
        elif 'friday' in text:
            return self.next_weekday(now, 4, self.extract_time(text))
        
        # Default to tomorrow at 9 AM
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    
    def extract_time(self, text: str) -> datetime:
        """Extract time from text"""
        import re
        
        # Look for time patterns
        time_pattern = r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?'
        match = re.search(time_pattern, text.lower())
        
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            ampm = match.group(3)
            
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            
            return datetime.now().replace(hour=hour, minute=minute)
        
        # Default time
        return datetime.now().replace(hour=9, minute=0)
    
    def next_weekday(self, d: datetime, weekday: int, time: datetime) -> datetime:
        """Get next occurrence of weekday"""
        days_ahead = weekday - d.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        target_date = d + timedelta(days=days_ahead)
        return target_date.replace(hour=time.hour, minute=time.minute, second=0, microsecond=0)
    
    def extract_location(self, text: str) -> str:
        """Extract location from text"""
        # Simple location extraction
        if ' at ' in text:
            parts = text.split(' at ')
            if len(parts) > 1:
                location_part = parts[-1].split()[0]
                if not any(word in location_part for word in ['am', 'pm', ':', 'o\'clock']):
                    return location_part.title()
        return ""
    
    def extract_contact_info(self, text: str) -> Optional[Dict]:
        """Extract contact information from text"""
        import re
        
        # Look for name patterns
        name_pattern = r'(?:add|contact)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        name_match = re.search(name_pattern, text, re.IGNORECASE)
        
        if not name_match:
            return None
        
        name = name_match.group(1)
        
        # Look for email
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        email_match = re.search(email_pattern, text)
        
        # Look for phone
        phone_pattern = r'(\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        phone_match = re.search(phone_pattern, text)
        
        return {
            "name": name,
            "email": email_match.group(1) if email_match else None,
            "phone": phone_match.group(1) if phone_match else None
        }
    
    def create_event(self, event_data: Dict) -> bool:
        """Create a calendar event"""
        try:
            event = CalendarEvent(
                title=event_data['title'],
                start_time=datetime.fromisoformat(event_data['start_time']),
                end_time=datetime.fromisoformat(event_data['end_time']) if event_data.get('end_time') else None,
                description=event_data.get('description', ''),
                location=event_data.get('location', ''),
                uid=str(uuid.uuid4())
            )
            
            self.events.append(event)
            self.save_events()
            print(f"✓ Created event: {event.title} at {event.start_time.strftime('%m/%d %H:%M')}")
            return True
        except Exception as e:
            print(f"❌ Error creating event: {e}")
            return False
    
    def create_todo(self, todo_data: Dict) -> bool:
        """Create a todo item"""
        try:
            todo = TodoItem(
                title=todo_data['title'],
                description=todo_data.get('description', ''),
                due_date=datetime.fromisoformat(todo_data['due_date']) if todo_data.get('due_date') else None,
                priority=todo_data.get('priority', 'normal'),
                uid=str(uuid.uuid4())
            )
            
            self.todos.append(todo)
            self.save_todos()
            print(f"✅ Created todo: {todo.title}")
            if todo.due_date:
                print(f"   Due: {todo.due_date.strftime('%m/%d %H:%M')}")
            return True
        except Exception as e:
            print(f"❌ Error creating todo: {e}")
            return False
    
    def create_contact(self, contact_data: Dict) -> bool:
        """Create a contact"""
        try:
            contact = Contact(
                name=contact_data['name'],
                phone=contact_data.get('phone'),
                email=contact_data.get('email'),
                company=contact_data.get('company'),
                uid=str(uuid.uuid4())
            )
            
            self.contacts.append(contact)
            self.save_contacts()
            print(f"📇 Created contact: {contact.name}")
            return True
        except Exception as e:
            print(f"❌ Error creating contact: {e}")
            return False
    
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
        """Get pending todos"""
        return [todo for todo in self.todos if not todo.completed]
    
    def search_contacts(self, query: str) -> List[Contact]:
        """Search contacts"""
        query = query.lower()
        return [
            contact for contact in self.contacts
            if (query in contact.name.lower() or
                (contact.email and query in contact.email.lower()) or
                (contact.phone and query in contact.phone))
        ]
    
    def process_input(self, user_input: str) -> str:
        """Process user input"""
        # Handle commands
        if user_input.lower().startswith('/'):
            return self.handle_command(user_input)
        
        # Parse and process
        result = self.simple_parse_input(user_input)
        
        # Create events
        for event_data in result.get("calendar_events", []):
            self.create_event(event_data)
        
        # Create todos
        for todo_data in result.get("todos", []):
            self.create_todo(todo_data)
        
        # Create contacts
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
            for event in events[:10]:
                response += f"• {event.title} - {event.start_time.strftime('%m/%d %H:%M')}"
                if event.location:
                    response += f" @ {event.location}"
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
                response += f" ({todo.priority})\n"
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
                response += "\n"
            return response
        
        elif command == '/help':
            return """🤖 Demo Assistant Commands:
/upcoming - Show upcoming events
/todos - Show pending todos  
/search <name> - Search contacts
/help - Show this help

Examples:
• "Meeting with John tomorrow at 3pm"
• "Remind me to call Sarah next Tuesday"
• "Add Jane Doe to contacts, email jane@company.com"
• "Lunch with team Friday at noon"
"""
        
        else:
            return "❓ Unknown command. Type /help for available commands."

def main():
    """Main demo interface"""
    print("🤖 Local Demo Personal Assistant")
    print("=" * 50)
    print("This is a simplified demo version that:")
    print("✓ Works completely offline")
    print("✓ Uses simple pattern matching instead of LLM")
    print("✓ Saves everything to local JSON files")
    print("✓ No external dependencies required")
    print()
    
    assistant = LocalPersonalAssistant()
    
    print("Type /help for commands or try natural language:")
    print("Examples: 'meeting tomorrow at 3pm', 'remind me to call John'")
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

if __name__ == "__main__":
    main()
