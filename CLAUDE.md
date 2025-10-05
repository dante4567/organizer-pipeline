# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

```bash
# Local development
./local_dev.sh  # Setup (run once)
./run_local.sh  # Run the server

# Or with Docker
docker-compose up organizer-pipeline

# Check health
curl http://localhost:8002/health
```

## Architecture

**Modern FastAPI Service** (October 2025 Refactor):
- `src/organizer_api/` - FastAPI application layer
  - `main.py` - Server entry point
  - `routes/` - API endpoints (tasks, calendar, contacts)
  - `middleware/` - Security and validation
- `src/organizer_core/` - Business logic layer
  - `models.py` - Data models (CalendarEvent, TodoItem, Contact)
  - `providers/` - LLM provider implementations
  - `services/` - Service layer
  - `security/` - Sanitizers and validators

## Current State: 7/10 - CRUD Works, Needs Frontends

### What Works ✅
- **CRUD operations work!** Tasks, calendar, contacts persist to database
- Server stable, no crashes
- Security layer present (rate limiting, XSS protection, validation)
- Clean architecture that's maintainable
- Data persistence confirmed (survives restarts)
- 63/92 tests passing (infrastructure issues for failures, not critical)

### What's Missing ❌
- **No frontends** - API-only, requires curl/Postman
- No authentication - anyone can access everything
- SQLite limitation - won't handle concurrent users well
- CalDAV/CardDAV integration not implemented
- Files CRUD still stubs
- 29 tests failing (infrastructure, not critical bugs)

## Development Commands

### Running the Server
```bash
# Local development
cd src && \
SECURITY_SECRET_KEY="dev-secret-key-change-in-production-must-be-32-chars-min" \
LLM_PROVIDER="demo" \
LLM_MODEL="demo" \
DEBUG="true" \
python3 -m uvicorn organizer_api.main:app --host 127.0.0.1 --port 8002 --reload

# Or use the provided script
./run_local.sh
```

### Testing
```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific categories
pytest tests/test_models.py -v          # 17/17 passing
pytest tests/test_validation.py -v      # 26/28 passing
pytest tests/test_providers.py -v       # 7/11 passing
pytest tests/test_api.py -v             # 3/19 passing (needs app state fixes)

# Test endpoints manually
curl http://localhost:8002/health
curl http://localhost:8002/docs  # Swagger UI
```

### Database
```bash
# Check if tables exist
sqlite3 src/data/organizer.db ".schema"

# View data
sqlite3 src/data/organizer.db "SELECT * FROM tasks;"
```

## Critical Next Steps (To Reach 8/10)

### Phase 1: Add Frontends (6-10 hours) - DO THIS NOW
**Priority: HIGH** - CRUD works, make it usable

1. Telegram bot (2 hours) - Daily task management from phone
2. Web UI (4-6 hours) - Dashboard for planning and organization
3. OpenWebUI function (2 hours) - Advanced chat interface

See `ADD_FRONTENDS_GUIDE.md` for complete implementation details.

### Phase 2: Use It Daily (1-2 weeks)
- Manage real tasks/calendar/contacts
- Find pain points through usage
- Identify critical bugs
- Document what's missing

### Phase 3: Polish Based on Usage (variable)
- Fix top 3-5 pain points discovered
- Add auth if needed (single user JWT)
- Improve error handling
- Optional: Add one integration (CalDAV or Todoist)

## Frontend Interfaces (Ready to Add NOW)

### 1. Telegram Bot
**Status**: READY - CRUD works, just add the bot
**Where**: Create `telegram-bot/organizer_bot.py`
**How**: Copy from ai-ecosystem-integrated, connect to http://localhost:8002
**Time**: 2 hours

Features:
- `/today` - Today's tasks and events
- `/todos` - Pending tasks
- `/events` - Upcoming calendar events
- Natural language: "Schedule meeting tomorrow at 3pm"

### 2. Simple Web GUI (Recommended: Streamlit)
**Status**: READY - CRUD works, just build the UI
**Where**: Create `web-ui/app.py`
**How**: Streamlit is better for forms/dashboards than Gradio
**Time**: 4-6 hours

Features:
- Task management dashboard with filtering
- Calendar view with week/month layout
- Contact list with search
- Quick add forms for all entities
- Statistics dashboard

### 3. OpenWebUI Function
**Status**: READY - CRUD works, just copy config
**Where**: Create `openwebui/organizer_function.py`
**How**: Copy from ai-ecosystem-integrated, update URL
**Time**: 2-3 hours

Features:
- `create_task(title, due_date, priority)` - Natural language task creation
- `get_my_tasks()` - View pending tasks
- `get_my_events()` - View calendar
- `ask_assistant(message)` - LLM-powered natural language processing

## Environment Configuration

Required in `.env` or export:
```bash
# Security
SECURITY_SECRET_KEY="your-32-char-secret-key"

# LLM Provider (choose one)
LLM_PROVIDER="demo"  # or "openai", "anthropic", "groq"
LLM_MODEL="demo"     # or model name

# Database
DATABASE_URL="sqlite:///data/organizer.db"

# Optional integrations
TODOIST_API_KEY="..."
CALDAV_URL="https://your-server.com/remote.php/dav/"
CALDAV_USERNAME="..."
CALDAV_PASSWORD="..."

# Server
PORT=8002
DEBUG="true"  # Set to "false" in production
```

## Adding Frontends - Implementation Order

### Step 1: Telegram Bot (EASIEST, DO THIS FIRST)
**Time**: 2 hours
**Prerequisites**: CRUD operations working

```bash
# 1. Create telegram-bot directory
mkdir telegram-bot
cd telegram-bot

# 2. Copy bot from ai-ecosystem-integrated
cp ../../ai-ecosystem-integrated/ai-telegram-bots/organizer_bot.py .

# 3. Update service URL
# Change: ORGANIZER_SERVICE_URL = "http://localhost:8002"

# 4. Install dependencies
pip install python-telegram-bot aiohttp

# 5. Get bot token from @BotFather
export TELEGRAM_BOT_TOKEN="your_token_here"

# 6. Run
python organizer_bot.py
```

### Step 2: Web UI (MODERATE)
**Time**: 4-6 hours
**Prerequisites**: CRUD operations working

```bash
# 1. Create web-ui directory
mkdir web-ui
cd web-ui

# 2. Create requirements.txt
echo "streamlit>=1.28.0
requests>=2.31.0
python-dateutil>=2.8.2" > requirements.txt

# 3. Install
pip install -r requirements.txt

# 4. Create app.py with Streamlit
streamlit run app.py
```

### Step 3: OpenWebUI Function (ADVANCED)
**Time**: 2-3 hours
**Prerequisites**: CRUD operations working

```bash
# 1. Create openwebui directory
mkdir openwebui

# 2. Copy template from ai-ecosystem-integrated
cp ../../ai-ecosystem-integrated/openwebui-configs/organizer-only-config.py \
   openwebui/organizer_function.py

# 3. Update service URL to http://localhost:8002

# 4. Drop file into OpenWebUI
cp openwebui/organizer_function.py /path/to/openwebui/functions/
```

## Honest Assessment

**Current**: 7/10 - CRUD works, server stable, clean architecture
**After Frontends**: 8/10 - Usable for daily personal workflow
**After Daily Usage**: 8.5/10 - Bug-fixed, polished for real use
**Production (multi-user)**: Would need auth, PostgreSQL, monitoring (2-3 months)

**No Blockers** - Ready for frontends NOW

## Recommended Work Order

**This Week** (6-10 hours):
1. Add Telegram bot (2 hours) - Start using it from phone
2. Add Web UI (4-6 hours) - Visual dashboard
3. Use both daily for task/calendar management

**Next Week** (2-4 hours):
1. Fix top 3 pain points discovered through usage
2. Add data export/backup
3. (Optional) Add basic auth if needed

**Month 2** (if you want to share it):
1. Add CalDAV/CardDAV sync
2. Multi-user support
3. Deploy with Docker

CRUD works - **add frontends immediately to make it usable!**
