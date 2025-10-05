# Web UI for Personal Organizer

Beautiful dashboard for task, calendar, and contact management.

## Setup

### 1. Install Dependencies
```bash
cd web-ui
pip install -r requirements.txt
```

### 2. Run
```bash
# Make sure organizer service is running first!
# In another terminal: cd ../src && python3 -m uvicorn organizer_api.main:app --host 127.0.0.1 --port 8000

streamlit run app.py
```

The UI will open at: **http://localhost:8501**

## Features

### 📋 Tasks Page
- Create tasks with title, description, priority, due date
- Filter by status (pending, in_progress, completed)
- Grouped by priority (urgent, high, medium, low)
- Quick actions: Complete, Delete
- Tag support

### 📅 Calendar Page
- Create events with start/end time, location
- View events in date range
- Filter by date

### 👥 Contacts Page
- Add contacts with name, email, phone, company
- Search across all fields
- Notes support

### 📊 Statistics Page
- Overview metrics (total tasks, events, contacts)
- Task breakdown by priority
- Task breakdown by status
- Visual charts

## Screenshots

### Tasks Dashboard
- Priority-coded task list
- One-click actions
- Tag visualization

### Calendar View
- Upcoming events
- Date range filtering
- Event details

## Configuration

Edit `app.py` line 7 to change API URL:
```python
ORGANIZER_URL = "http://localhost:8000"  # Change if running on different port
```

## Troubleshooting

**"Service is not running!" error:**
- Start the organizer API first
- Check it's running: `curl http://localhost:8000/api/v1/tasks/`

**Tasks not showing up:**
- Check browser console for errors
- Verify API is responding: `curl http://localhost:8000/api/v1/tasks/`
- Click the "⟳" button in Streamlit to reload

**Changes not saving:**
- Check API logs for errors
- Verify database is writable: `ls -la src/data/organizer.db`

## Known Limits

- No authentication (anyone with URL access can use it)
- No real-time updates (must refresh manually)
- SQLite means single user only
- No task editing (must delete and recreate)
