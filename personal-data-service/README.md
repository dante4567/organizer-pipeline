# Personal Data Management Service

A complete, standalone FastAPI service for managing calendar events, tasks, contacts, and files with natural language processing capabilities.

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone or download the service files
cd personal-data-service

# Build and start the service
docker-compose up -d

# The service will be available at http://localhost:8002
curl http://localhost:8002/health
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export ANTHROPIC_API_KEY="your-claude-api-key"
export OPENAI_API_KEY="your-openai-api-key"

# Run the service
python app.py
```

## 📋 Features

### Core Functionality
- **📅 Calendar Management** - Events with reminders, recurring events, attendees
- **✅ Task Management** - Priority-based tasks with status tracking
- **📇 Contact Management** - Full contact information with search capabilities
- **📁 File Management** - Browse and manage files within data directory
- **🧠 Natural Language Processing** - Parse commands like "Schedule meeting tomorrow at 2pm"
- **⏰ Background Services** - Automatic reminders and notifications

### API Endpoints

#### Calendar
- `POST /calendar/events` - Create event
- `GET /calendar/events` - List events (with time filters)
- `GET /calendar/today` - Get today's events
- `GET /calendar/events/{id}` - Get specific event
- `PUT /calendar/events/{id}` - Update event
- `DELETE /calendar/events/{id}` - Delete event

#### Tasks
- `POST /tasks` - Create task
- `GET /tasks` - List tasks (with status filter)
- `GET /tasks/{id}` - Get specific task
- `PUT /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task

#### Contacts
- `POST /contacts` - Create contact
- `GET /contacts` - List contacts (with search)
- `GET /contacts/{id}` - Get specific contact
- `PUT /contacts/{id}` - Update contact
- `DELETE /contacts/{id}` - Delete contact

#### Files
- `GET /files` - List files in directory
- `GET /files/info` - Get file information

#### Natural Language
- `POST /process/natural` - Process natural language commands

#### Summary & Stats
- `GET /summary/today` - Get today's summary
- `GET /stats` - Get service statistics
- `GET /health` - Health check

## 🛠️ Configuration

### Environment Variables

```bash
# API Keys (at least one required for NLP)
ANTHROPIC_API_KEY=sk-ant-api03-...  # Claude API key
OPENAI_API_KEY=sk-...               # OpenAI API key

# Storage Configuration
DB_PATH=/data/personal.db           # SQLite database path
FILES_ROOT=/data/files              # Files directory

# Service Configuration
DEFAULT_LLM=anthropic               # or "openai"
REMINDER_CHECK_MINUTES=5            # Reminder check interval
DAILY_REVIEW_HOUR=8                 # Daily review time (24h format)
TIMEZONE=UTC                        # Timezone for scheduling
```

### Using .env File

Create a `.env` file in the project directory:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
DEFAULT_LLM=anthropic
DB_PATH=/data/personal.db
FILES_ROOT=/data/files
```

## 📊 Usage Examples

### Calendar Management

```bash
# Create an event
curl -X POST "http://localhost:8002/calendar/events" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Meeting",
    "start_time": "2024-01-15T14:00:00",
    "end_time": "2024-01-15T15:00:00",
    "location": "Conference Room A",
    "event_type": "meeting",
    "attendees": ["john@company.com"],
    "reminder_minutes": 15
  }'

# Get today's events
curl "http://localhost:8002/calendar/today"
```

### Task Management

```bash
# Create a task
curl -X POST "http://localhost:8002/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project documentation",
    "description": "Finish writing the API documentation",
    "priority": "high",
    "due_date": "2024-01-20T17:00:00",
    "tags": ["documentation", "urgent"]
  }'

# Get pending tasks
curl "http://localhost:8002/tasks?status=pending"
```

### Natural Language Processing

```bash
# Schedule a meeting
curl -X POST "http://localhost:8002/process/natural" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Schedule a meeting with Sarah tomorrow at 3pm in the conference room"
  }'

# Create a task
curl -X POST "http://localhost:8002/process/natural" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Remind me to call the dentist next Friday, high priority"
  }'
```

## 🔌 OpenWebUI Integration

Use these functions in OpenWebUI for seamless integration:

```python
def manage_calendar(command: str):
    """Manage calendar events using natural language"""
    import requests
    response = requests.post(
        "http://localhost:8002/process/natural",
        json={"text": command}
    )
    return response.json() if response.status_code == 200 else f"Error: {response.status_code}"

def quick_task(title: str, priority: str = "medium"):
    """Quickly create a task"""
    import requests
    response = requests.post(
        "http://localhost:8002/tasks",
        json={"title": title, "priority": priority}
    )
    return f"Task created: {title}" if response.status_code == 200 else "Failed to create task"

def get_today_summary():
    """Get today's events and pending tasks"""
    import requests

    events_response = requests.get("http://localhost:8002/calendar/today")
    tasks_response = requests.get("http://localhost:8002/tasks?status=pending&limit=5")

    summary = "📅 Today's Schedule:\\n"
    if events_response.status_code == 200:
        events = events_response.json()['events']
        for event in events:
            summary += f"• {event['start_time']}: {event['title']}\\n"

    summary += "\\n✅ Pending Tasks:\\n"
    if tasks_response.status_code == 200:
        tasks = tasks_response.json()['tasks']
        for task in tasks[:5]:
            summary += f"• [{task['priority']}] {task['title']}\\n"

    return summary
```

## 🧪 Testing

### Run the Test Suite

```bash
# Make sure the service is running
docker-compose up -d

# Run tests
python test_personal.py

# Or run specific test functions
python -c "from test_personal import test_calendar; test_calendar()"
```

### Manual Testing

```bash
# Health check
curl http://localhost:8002/health

# Check service statistics
curl http://localhost:8002/stats

# Get today's summary
curl http://localhost:8002/summary/today
```

## 📁 Project Structure

```
personal-data-service/
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Service orchestration
├── test_personal.py      # Comprehensive test suite
├── README.md             # This file
├── .env                  # Environment variables (create this)
└── data/                 # Persistent data (auto-created)
    ├── personal.db       # SQLite database
    └── files/            # File storage directory
```

## 🔧 Database Schema

The service uses SQLite with the following tables:

- **calendar_events** - Calendar events with reminders
- **tasks** - Task management with priorities and status
- **contacts** - Contact information with search capabilities
- **reminders** - Notification tracking

## 🔄 Background Services

The service includes background schedulers for:

- **Reminder Checks** - Every 5 minutes (configurable)
- **Daily Reviews** - At 8:00 AM (configurable)
- **Overdue Task Detection** - Automatic monitoring

## 🚨 Error Handling

The service includes comprehensive error handling:

- **Validation Errors** (422) - Invalid request data
- **Not Found Errors** (404) - Resource doesn't exist
- **Server Errors** (500) - Internal server issues
- **Graceful Fallbacks** - NLP works without API keys

## 🔐 Security Considerations

- **Path Validation** - Prevents directory traversal attacks
- **Input Sanitization** - All inputs are validated
- **CORS Enabled** - Configured for web integration
- **Health Checks** - Container health monitoring

## 📈 Performance

- **SQLite Database** - Fast, embedded database
- **Async FastAPI** - High-performance async operations
- **Connection Pooling** - Efficient database access
- **Background Tasks** - Non-blocking reminders

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs personal-service

# Verify port availability
lsof -i :8002

# Check database permissions
ls -la data/
```

### NLP Not Working

1. Verify API key is set: `echo $ANTHROPIC_API_KEY`
2. Check logs for API errors
3. Service works with fallback parsing if no API key

### Database Issues

```bash
# Check database file
ls -la data/personal.db

# View database contents
sqlite3 data/personal.db ".tables"
```

## 📚 API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8002/docs
- **OpenAPI Schema**: http://localhost:8002/openapi.json

## 🤝 Integration Examples

### Python Client

```python
import requests

class PersonalDataClient:
    def __init__(self, base_url="http://localhost:8002"):
        self.base_url = base_url

    def create_event(self, title, start_time, **kwargs):
        data = {"title": title, "start_time": start_time, **kwargs}
        return requests.post(f"{self.base_url}/calendar/events", json=data)

    def process_natural_language(self, text):
        return requests.post(f"{self.base_url}/process/natural", json={"text": text})

# Usage
client = PersonalDataClient()
result = client.process_natural_language("Schedule lunch tomorrow at noon")
```

### JavaScript Client

```javascript
class PersonalDataAPI {
    constructor(baseURL = 'http://localhost:8002') {
        this.baseURL = baseURL;
    }

    async createTask(title, priority = 'medium') {
        const response = await fetch(`${this.baseURL}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, priority })
        });
        return response.json();
    }

    async getTodaysSummary() {
        const response = await fetch(`${this.baseURL}/summary/today`);
        return response.json();
    }
}
```

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues, questions, or contributions:

1. Check the logs: `docker-compose logs`
2. Run the test suite: `python test_personal.py`
3. Verify configuration: `curl http://localhost:8002/health`

---

**🎉 Your personal data management service is ready to use!**

Start with simple commands like:
- "What's on my calendar today?"
- "Create a task to review the quarterly report"
- "Add John Smith to my contacts"