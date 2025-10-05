import streamlit as st
import requests
from datetime import datetime, timedelta
import json

ORGANIZER_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Personal Organizer",
    page_icon="📋",
    layout="wide"
)

# Helper functions
def check_health():
    """Check if service is healthy"""
    try:
        response = requests.get(f"{ORGANIZER_URL}/api/v1/tasks/", timeout=5)
        return response.status_code == 200
    except:
        return False

def create_task(title, description, priority, due_date, tags):
    """Create a new task"""
    payload = {
        "title": title,
        "description": description,
        "priority": priority,
        "status": "pending",
        "tags": [tag.strip() for tag in tags.split(",") if tag.strip()]
    }
    if due_date:
        payload["due_date"] = due_date.isoformat()

    response = requests.post(f"{ORGANIZER_URL}/api/v1/tasks/", json=payload)
    return response.json() if response.status_code in (200, 201) else None

def get_tasks(status=None):
    """Get tasks"""
    url = f"{ORGANIZER_URL}/api/v1/tasks/"
    if status:
        url += f"?status={status}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else []

def update_task(task_id, updates):
    """Update a task"""
    response = requests.put(f"{ORGANIZER_URL}/api/v1/tasks/{task_id}", json=updates)
    return response.status_code == 200

def delete_task(task_id):
    """Delete a task"""
    response = requests.delete(f"{ORGANIZER_URL}/api/v1/tasks/{task_id}")
    return response.status_code in (200, 204)

def create_event(title, start_time, end_time, description, location):
    """Create calendar event"""
    payload = {
        "title": title,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "description": description,
        "location": location
    }
    response = requests.post(f"{ORGANIZER_URL}/api/v1/calendar/events", json=payload)
    return response.json() if response.status_code in (200, 201) else None

def get_events(start_date=None, end_date=None):
    """Get calendar events"""
    params = {}
    if start_date:
        params["start_after"] = start_date.isoformat()
    if end_date:
        params["start_before"] = end_date.isoformat()

    response = requests.get(f"{ORGANIZER_URL}/api/v1/calendar/events", params=params)
    return response.json() if response.status_code == 200 else []

def create_contact(name, email, phone, company, notes):
    """Create contact"""
    payload = {
        "name": name,
        "email": email if email else None,
        "phone": phone if phone else None,
        "company": company if company else None,
        "notes": notes if notes else None
    }
    response = requests.post(f"{ORGANIZER_URL}/api/v1/contacts/", json=payload)
    return response.json() if response.status_code in (200, 201) else None

def get_contacts():
    """Get all contacts"""
    response = requests.get(f"{ORGANIZER_URL}/api/v1/contacts/")
    return response.json() if response.status_code == 200 else []

# Main app
st.title("📋 Personal Organizer")
st.markdown("*Task management, calendar, and contacts*")

# Health check
if not check_health():
    st.error("⚠️ Service is not running! Start it with:")
    st.code("cd src && python3 -m uvicorn organizer_api.main:app --host 127.0.0.1 --port 8000")
    st.stop()

st.success("✅ Service is healthy")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Go to:",
        ["📋 Tasks", "📅 Calendar", "👥 Contacts", "📊 Statistics"]
    )

# Tasks Page
if page == "📋 Tasks":
    st.header("Tasks")

    # Create new task
    with st.expander("➕ Create New Task", expanded=False):
        with st.form("new_task"):
            col1, col2 = st.columns(2)
            with col1:
                task_title = st.text_input("Title*", placeholder="Buy groceries")
                task_priority = st.selectbox(
                    "Priority",
                    ["low", "medium", "high", "urgent"]
                )
            with col2:
                task_due = st.date_input("Due Date (optional)", value=None)
                task_tags = st.text_input("Tags (comma-separated)", placeholder="personal, shopping")

            task_description = st.text_area("Description", placeholder="Details about the task...")

            submitted = st.form_submit_button("Create Task", type="primary")
            if submitted and task_title:
                result = create_task(
                    task_title,
                    task_description,
                    task_priority,
                    task_due if task_due else None,
                    task_tags
                )
                if result:
                    st.success(f"✅ Task created: {task_title}")
                    st.rerun()
                else:
                    st.error("Failed to create task")

    # Filter tasks
    st.subheader("Your Tasks")
    filter_status = st.selectbox(
        "Filter by status:",
        ["all", "pending", "in_progress", "completed"],
        index=0
    )

    # Get and display tasks
    tasks = get_tasks(None if filter_status == "all" else filter_status)

    if not tasks:
        st.info("No tasks found. Create one above!")
    else:
        # Group by priority
        urgent_tasks = [t for t in tasks if t.get("priority") == "urgent"]
        high_tasks = [t for t in tasks if t.get("priority") == "high"]
        medium_tasks = [t for t in tasks if t.get("priority") == "medium"]
        low_tasks = [t for t in tasks if t.get("priority") == "low"]

        for priority_name, priority_tasks in [
            ("🔴 Urgent", urgent_tasks),
            ("🟠 High Priority", high_tasks),
            ("🟡 Medium Priority", medium_tasks),
            ("🟢 Low Priority", low_tasks)
        ]:
            if priority_tasks:
                st.markdown(f"### {priority_name}")
                for task in priority_tasks:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])

                        with col1:
                            st.markdown(f"**{task['title']}**")
                            if task.get('description'):
                                st.caption(task['description'])
                            if task.get('tags'):
                                st.caption(f"Tags: {', '.join(task['tags'])}")

                        with col2:
                            if task.get('due_date'):
                                due = datetime.fromisoformat(task['due_date'].replace('Z', '+00:00'))
                                st.caption(f"Due: {due.strftime('%Y-%m-%d')}")
                            st.caption(f"Status: {task['status']}")

                        with col3:
                            if task['status'] != 'completed':
                                if st.button("✅ Complete", key=f"complete_{task['id']}"):
                                    task['status'] = 'completed'
                                    if update_task(task['id'], task):
                                        st.rerun()

                            if st.button("🗑️ Delete", key=f"delete_{task['id']}"):
                                if delete_task(task['id']):
                                    st.rerun()

                        st.divider()

# Calendar Page
elif page == "📅 Calendar":
    st.header("Calendar")

    # Create new event
    with st.expander("➕ Create New Event", expanded=False):
        with st.form("new_event"):
            event_title = st.text_input("Title*", placeholder="Team Meeting")

            col1, col2 = st.columns(2)
            with col1:
                event_date = st.date_input("Date")
                event_start_time = st.time_input("Start Time")
            with col2:
                event_end_date = st.date_input("End Date", value=event_date)
                event_end_time = st.time_input("End Time")

            event_location = st.text_input("Location", placeholder="Conference Room A")
            event_description = st.text_area("Description")

            submitted = st.form_submit_button("Create Event", type="primary")
            if submitted and event_title:
                start_datetime = datetime.combine(event_date, event_start_time)
                end_datetime = datetime.combine(event_end_date, event_end_time)

                result = create_event(
                    event_title,
                    start_datetime,
                    end_datetime,
                    event_description,
                    event_location
                )
                if result:
                    st.success(f"✅ Event created: {event_title}")
                    st.rerun()
                else:
                    st.error("Failed to create event")

    # View events
    st.subheader("Upcoming Events")

    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        filter_start = st.date_input("From", value=datetime.now().date())
    with col2:
        filter_end = st.date_input("To", value=datetime.now().date() + timedelta(days=7))

    events = get_events(
        datetime.combine(filter_start, datetime.min.time()),
        datetime.combine(filter_end, datetime.max.time())
    )

    if not events:
        st.info("No events found in this date range.")
    else:
        for event in events:
            with st.container():
                start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(event['end_time'].replace('Z', '+00:00'))

                st.markdown(f"### {event['title']}")
                st.caption(f"📅 {start.strftime('%Y-%m-%d %H:%M')} - {end.strftime('%H:%M')}")

                if event.get('location'):
                    st.caption(f"📍 {event['location']}")
                if event.get('description'):
                    st.write(event['description'])

                st.divider()

# Contacts Page
elif page == "👥 Contacts":
    st.header("Contacts")

    # Create new contact
    with st.expander("➕ Add New Contact", expanded=False):
        with st.form("new_contact"):
            col1, col2 = st.columns(2)
            with col1:
                contact_name = st.text_input("Name*", placeholder="John Doe")
                contact_email = st.text_input("Email", placeholder="john@example.com")
            with col2:
                contact_phone = st.text_input("Phone", placeholder="+1234567890")
                contact_company = st.text_input("Company", placeholder="Acme Corp")

            contact_notes = st.text_area("Notes")

            submitted = st.form_submit_button("Add Contact", type="primary")
            if submitted and contact_name:
                result = create_contact(
                    contact_name,
                    contact_email,
                    contact_phone,
                    contact_company,
                    contact_notes
                )
                if result:
                    st.success(f"✅ Contact added: {contact_name}")
                    st.rerun()
                else:
                    st.error("Failed to add contact")

    # Display contacts
    st.subheader("Your Contacts")
    contacts = get_contacts()

    if not contacts:
        st.info("No contacts found. Add one above!")
    else:
        # Search
        search = st.text_input("🔍 Search contacts", placeholder="Search by name, email, company...")

        filtered_contacts = contacts
        if search:
            search_lower = search.lower()
            filtered_contacts = [
                c for c in contacts
                if search_lower in c.get('name', '').lower()
                or search_lower in str(c.get('email', '')).lower()
                or search_lower in str(c.get('company', '')).lower()
            ]

        for contact in filtered_contacts:
            with st.container():
                st.markdown(f"### {contact['name']}")

                col1, col2 = st.columns(2)
                with col1:
                    if contact.get('email'):
                        st.caption(f"📧 {contact['email']}")
                    if contact.get('phone'):
                        st.caption(f"📞 {contact['phone']}")
                with col2:
                    if contact.get('company'):
                        st.caption(f"🏢 {contact['company']}")

                if contact.get('notes'):
                    st.write(contact['notes'])

                st.divider()

# Statistics Page
elif page == "📊 Statistics":
    st.header("Statistics")

    tasks = get_tasks()
    events = get_events()
    contacts = get_contacts()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Tasks", len(tasks))
        pending = len([t for t in tasks if t['status'] == 'pending'])
        st.metric("Pending Tasks", pending)

    with col2:
        st.metric("Total Events", len(events))
        upcoming = len([
            e for e in events
            if datetime.fromisoformat(e['start_time'].replace('Z', '+00:00')) > datetime.now()
        ])
        st.metric("Upcoming Events", upcoming)

    with col3:
        st.metric("Total Contacts", len(contacts))

    # Task breakdown by priority
    st.subheader("Tasks by Priority")
    priority_counts = {
        "urgent": len([t for t in tasks if t.get('priority') == 'urgent']),
        "high": len([t for t in tasks if t.get('priority') == 'high']),
        "medium": len([t for t in tasks if t.get('priority') == 'medium']),
        "low": len([t for t in tasks if t.get('priority') == 'low'])
    }
    st.bar_chart(priority_counts)

    # Task breakdown by status
    st.subheader("Tasks by Status")
    status_counts = {
        "pending": len([t for t in tasks if t['status'] == 'pending']),
        "in_progress": len([t for t in tasks if t['status'] == 'in_progress']),
        "completed": len([t for t in tasks if t['status'] == 'completed'])
    }
    st.bar_chart(status_counts)

# Footer
st.markdown("---")
st.caption("**Current State:** 7/10 - CRUD works, no auth, single user")
st.caption("**Known Limits:** SQLite (no concurrent users) | No CalDAV sync | API-only auth")
