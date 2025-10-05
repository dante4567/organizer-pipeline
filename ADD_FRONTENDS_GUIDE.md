# Adding Frontends to Organizer Pipeline

**Date**: October 5, 2025
**Current State**: 7/10 - CRUD works, needs frontends for usability
**Goal**: Make the working API actually usable via Telegram + Web UI

---

## Current Reality Check

**What Works** ✅:
- Tasks CRUD - fully tested, persistence confirmed
- Calendar CRUD - basic testing, works
- Contacts CRUD - basic testing, works
- Server stable, no crashes
- Security layer present

**What's Missing** ❌:
- No frontend (API-only, requires curl)
- No auth (anyone can access)
- SQLite (single user only)

**Translation**: You built a perfectly good engine with no steering wheel. Let's add steering wheels.

---

## Why Add Frontends Now

The CRUD operations work. The server persists data. You can create tasks, but only via curl.

**Frontends turn this from "technical demo" to "daily tool".**

---

## Architecture Decision

**These frontends are STANDALONE** - they connect directly to organizer service at `http://localhost:8002`

```
organizer-pipeline/       # This repo - standalone frontends
├── telegram-bot/         # Connect to localhost:8002
└── web-ui/              # Connect to localhost:8002

ai-ecosystem-integrated/  # Other repo - has unified versions
└── ai-telegram-bots/
    └── unified_bot.py    # Uses gateway at localhost:8003
```

---

## Implementation Order

### 1. Telegram Bot (2 hours) - DO THIS FIRST

**Why first?** Easiest way to actually use the service. Create tasks from your phone.

**Steps**:

```bash
cd /path/to/organizer-pipeline
mkdir telegram-bot
cd telegram-bot
```

**Copy from ecosystem**:
```bash
cp ../../ai-ecosystem-integrated/ai-telegram-bots/organizer_bot.py .
```

**Check line ~25** - should be:
```python
ORGANIZER_SERVICE_URL = os.getenv("ORGANIZER_SERVICE_URL", "http://localhost:8002")
```

**Create `telegram-bot/requirements.txt`**:
```
python-telegram-bot==20.6
aiohttp>=3.8.0
python-dateutil>=2.8.2
```

**Setup and run**:
```bash
pip install -r requirements.txt

# Get bot token from @BotFather on Telegram
export TELEGRAM_BOT_TOKEN="your_token_here"

# Make sure organizer service is running
cd .. && ./run_local.sh  # or your startup script

# Run bot (in another terminal)
cd telegram-bot
python organizer_bot.py
```

**Test**:
- Send `/start` to your bot
- Try: "Create task: Buy groceries, due tomorrow"
- Try: `/todos` to see your tasks
- Try: "Schedule meeting tomorrow at 3pm"
- Try: `/today` for daily overview

### 2. Web UI with Streamlit (4-6 hours) - DO THIS NEXT

**Why Streamlit?** Better for forms/dashboards than Gradio. Perfect for task management.

**Steps**:

```bash
cd /path/to/organizer-pipeline
mkdir web-ui
cd web-ui
```

**Create `web-ui/requirements.txt`**:
```
streamlit>=1.28.0
requests>=2.31.0
python-dateutil>=2.8.2
```

**Create `web-ui/app.py`**:

```python
import streamlit as st
import requests
from datetime import datetime, timedelta
import json

ORGANIZER_URL = "http://localhost:8002"

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
        response = requests.get(f"{ORGANIZER_URL}/health", timeout=5)
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
    return response.json() if response.status_code == 200 else None

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
    return response.status_code == 200

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
    return response.json() if response.status_code == 200 else None

def get_events(start_date=None, end_date=None):
    """Get calendar events"""
    params = {}
    if start_date:
        params["start"] = start_date.isoformat()
    if end_date:
        params["end"] = end_date.isoformat()

    response = requests.get(f"{ORGANIZER_URL}/api/v1/calendar/events", params=params)
    return response.json() if response.status_code == 200 else []

def create_contact(name, email, phone, company, notes):
    """Create contact"""
    payload = {
        "name": name,
        "email": email,
        "phone": phone,
        "company": company,
        "notes": notes
    }
    response = requests.post(f"{ORGANIZER_URL}/api/v1/contacts/", json=payload)
    return response.json() if response.status_code == 200 else None

def get_contacts():
    """Get all contacts"""
    response = requests.get(f"{ORGANIZER_URL}/api/v1/contacts/")
    return response.json() if response.status_code == 200 else []

# Main app
st.title("📋 Personal Organizer")
st.markdown("*Task management, calendar, and contacts*")

# Health check
if not check_health():
    st.error("⚠️ Service is not running! Start it with `./run_local.sh`")
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
                task_due = st.date_input("Due Date (optional)")
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
                                    if update_task(task['id'], {"status": "completed"}):
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
                or search_lower in c.get('email', '').lower()
                or search_lower in c.get('company', '').lower()
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
```

**Run**:
```bash
pip install -r requirements.txt

# Make sure organizer service is running
cd .. && ./run_local.sh

# Run web UI (in another terminal)
cd web-ui
streamlit run app.py
```

Access at: http://localhost:8501

### 3. OpenWebUI Function (2-3 hours) - OPTIONAL

**When**: After testing with Telegram + Web UI

```bash
cd /path/to/organizer-pipeline
mkdir openwebui
```

**Copy from ecosystem**:
```bash
cp ../../ai-ecosystem-integrated/openwebui-configs/organizer-only-config.py \
   openwebui/organizer_function.py
```

Check it points to `localhost:8002` (should already be correct).

---

## Testing Strategy

### Week 1: Daily Usage

**Goal**: Actually use it for real task/calendar management

**Using Telegram**:
- Morning: Check `/today` for daily overview
- Throughout day: Add tasks as they come up
- Evening: Mark completed tasks

**Using Web UI**:
- Weekly planning: Create events for next week
- Task review: Organize and prioritize tasks
- Contact management: Add contacts as you meet people

**What to monitor**:
1. **Persistence**: Does data survive restarts?
2. **Edge cases**: What happens with invalid input?
3. **Usability**: What's annoying? What's missing?
4. **Performance**: Any slow operations?

### Week 2: Stress Test

- Create 100 tasks
- Create 50 events
- Add 30 contacts
- Try to break it with weird input
- Test concurrent access (multiple browser tabs)

---

## Known Limitations

From the 7/10 assessment:

**Works Well** ✅:
- Happy path CRUD
- Data persistence
- Server stability

**Known Issues** ⚠️:
- No authentication (anyone can access)
- SQLite (single user, no concurrency)
- 29/92 tests failing (infrastructure, not critical)
- No CalDAV/CardDAV sync
- Files CRUD still stubs

**Unknown** ❓:
- Update/delete edge cases
- Stress test behavior
- Concurrent user handling
- Large data sets (1000+ tasks)

---

## Success Criteria

**After 2 weeks of daily usage**:

- ✅ Used for real task/calendar management
- ✅ Data never lost (survives restarts)
- ✅ Identified pain points
- ✅ Fixed critical bugs
- ✅ Actually useful in daily workflow

**Grade target**: 8/10 → "Usable for personal daily workflow"

---

## What NOT to Do Yet

**Don't add features**:
- ❌ Don't implement auth (not needed for single user)
- ❌ Don't migrate to PostgreSQL (SQLite fine for personal use)
- ❌ Don't build CalDAV sync (complex, use frontends first)

**Do use it heavily**:
- ✅ Add frontends
- ✅ Use daily for 2 weeks
- ✅ Document what breaks
- ✅ Fix critical issues only

---

## Next Steps

**Today** (2 hours):
1. Add Telegram bot
2. Create 5 tasks via Telegram
3. Check they persist (restart server, query via curl)

**This Week** (6-8 hours):
1. Add Web UI
2. Use both frontends daily
3. Create real tasks/events/contacts

**Next Week**:
1. Fix top 3 pain points
2. Decide: personal use only, or build for others?

---

**Start with Telegram bot - 2 hours to actually use what you built!**
