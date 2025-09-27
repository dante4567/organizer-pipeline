"""
OpenWebUI Integration Functions for Personal Data Service

Copy these functions into your OpenWebUI Functions section to integrate
with the Personal Data Management Service.
"""

def manage_calendar(command: str):
    """
    Manage calendar events using natural language.

    Examples:
        - "Schedule meeting tomorrow at 2pm"
        - "What's on my calendar today?"
        - "Cancel the 3pm meeting"
    """
    import requests

    try:
        response = requests.post(
            "http://localhost:8002/process/natural",
            json={"text": command},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Command processed successfully")
        else:
            return f"Failed to process: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error connecting to personal data service: {str(e)}"

def quick_task(title: str, priority: str = "medium"):
    """
    Quickly create a task.

    Args:
        title: Task title
        priority: low, medium, high, or urgent
    """
    import requests

    try:
        response = requests.post(
            "http://localhost:8002/tasks",
            json={"title": title, "priority": priority},
            timeout=10
        )

        if response.status_code == 200:
            task_id = response.json().get("task_id")
            return f"✅ Task created: {title} (ID: {task_id})"
        else:
            return f"❌ Failed to create task: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_today_summary():
    """Get today's events and pending tasks."""
    import requests

    try:
        # Get today's events
        events_response = requests.get("http://localhost:8002/calendar/today", timeout=10)
        tasks_response = requests.get("http://localhost:8002/tasks?status=pending&limit=5", timeout=10)

        summary = "📅 **Today's Schedule:**\\n"

        if events_response.status_code == 200:
            events = events_response.json().get('events', [])
            if events:
                for event in events:
                    start_time = event['start_time'][:16].replace('T', ' ')  # Format: YYYY-MM-DD HH:MM
                    summary += f"• {start_time}: {event['title']}"
                    if event.get('location'):
                        summary += f" @ {event['location']}"
                    summary += "\\n"
            else:
                summary += "• No events scheduled\\n"
        else:
            summary += "• Could not fetch events\\n"

        summary += "\\n✅ **Pending Tasks:**\\n"

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get('tasks', [])
            if tasks:
                for task in tasks[:5]:
                    summary += f"• [{task['priority']}] {task['title']}"
                    if task.get('due_date'):
                        due_date = task['due_date'][:10]  # Format: YYYY-MM-DD
                        summary += f" (Due: {due_date})"
                    summary += "\\n"
            else:
                summary += "• No pending tasks\\n"
        else:
            summary += "• Could not fetch tasks\\n"

        return summary

    except Exception as e:
        return f"❌ Error getting summary: {str(e)}"

def add_contact(name: str, email: str = "", phone: str = "", company: str = ""):
    """
    Add a new contact to the personal data service.

    Args:
        name: Contact name (required)
        email: Email address
        phone: Phone number
        company: Company name
    """
    import requests

    try:
        contact_data = {
            "name": name,
            "email": email if email else None,
            "phone": phone if phone else None,
            "company": company if company else None
        }

        response = requests.post(
            "http://localhost:8002/contacts",
            json=contact_data,
            timeout=10
        )

        if response.status_code == 200:
            contact_id = response.json().get("contact_id")
            return f"📇 Contact added: {name} (ID: {contact_id})"
        else:
            return f"❌ Failed to add contact: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def search_contacts(query: str):
    """
    Search contacts by name, email, or company.

    Args:
        query: Search term
    """
    import requests

    try:
        response = requests.get(
            f"http://localhost:8002/contacts?search={query}",
            timeout=10
        )

        if response.status_code == 200:
            contacts = response.json().get('contacts', [])
            if contacts:
                result = f"📇 Found {len(contacts)} contact(s):\\n"
                for contact in contacts[:10]:  # Limit to 10 results
                    result += f"• **{contact['name']}**"
                    if contact.get('email'):
                        result += f" - {contact['email']}"
                    if contact.get('phone'):
                        result += f" - {contact['phone']}"
                    if contact.get('company'):
                        result += f" ({contact['company']})"
                    result += "\\n"
                return result
            else:
                return f"📇 No contacts found for '{query}'"
        else:
            return f"❌ Search failed: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def schedule_event(title: str, date: str, time: str = "09:00", location: str = ""):
    """
    Schedule a calendar event.

    Args:
        title: Event title
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (default: 09:00)
        location: Event location
    """
    import requests
    from datetime import datetime, timedelta

    try:
        # Parse and format the datetime
        start_datetime = f"{date}T{time}:00"
        start_dt = datetime.fromisoformat(start_datetime)
        end_dt = start_dt + timedelta(hours=1)  # Default 1-hour duration

        event_data = {
            "title": title,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "location": location if location else None,
            "event_type": "meeting"
        }

        response = requests.post(
            "http://localhost:8002/calendar/events",
            json=event_data,
            timeout=10
        )

        if response.status_code == 200:
            event_id = response.json().get("event_id")
            return f"📅 Event scheduled: {title} on {date} at {time} (ID: {event_id})"
        else:
            return f"❌ Failed to schedule event: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_service_stats():
    """Get statistics about the personal data service."""
    import requests

    try:
        response = requests.get("http://localhost:8002/stats", timeout=10)

        if response.status_code == 200:
            stats = response.json()
            return f"""📊 **Personal Data Service Statistics:**

📅 **Calendar:** {stats['total_events']} total events, {stats['today_events']} today
✅ **Tasks:** {stats['total_tasks']} total, {stats['pending_tasks']} pending
📇 **Contacts:** {stats['total_contacts']} total

*Last updated: {stats['generated_at'][:19].replace('T', ' ')}*"""
        else:
            return f"❌ Failed to get stats: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def check_service_health():
    """Check if the personal data service is running."""
    import requests

    try:
        response = requests.get("http://localhost:8002/health", timeout=5)

        if response.status_code == 200:
            health = response.json()
            status = health.get('status', 'unknown')
            services = health.get('services', {})

            result = f"🔋 **Service Status:** {status}\\n"
            result += f"📊 **Database:** {services.get('database', 'unknown')}\\n"
            result += f"⏰ **Scheduler:** {services.get('scheduler', 'unknown')}\\n"
            result += f"🧠 **LLM:** {services.get('llm', 'unknown')}\\n"

            return result
        else:
            return f"❌ Service unhealthy: {response.status_code}"
    except Exception as e:
        return f"❌ Service not available: {str(e)}"