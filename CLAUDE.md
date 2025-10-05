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

## Current State: 4/10 (Phase 1 Complete)

### What Works ✅
- Server runs successfully on http://localhost:8002
- All API endpoints respond (no 500 errors)
- Security middleware working
- 92 tests written, 63 passing (68.5%)
- Data models validated (17/17 tests passing)
- Demo LLM provider functional

### What's Missing ❌
- **No CRUD operations** - Endpoints exist but don't save/retrieve data
- Database tables probably don't exist
- CalDAV/CardDAV integration planned but not implemented
- File monitoring not started
- **No frontends**

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

## Critical Next Steps (To Reach 7/10)

### Phase 2: Implement CRUD Operations (4-6 hours)
**Priority: CRITICAL** - Nothing works without this

1. Create database tables (1 hour)
2. Implement task CRUD (2 hours)
3. Implement calendar CRUD (1 hour)
4. Implement contact CRUD (1 hour)
5. Test manually (1 hour)

After this, you'll be able to actually save and retrieve data.

### Phase 3: Add One Integration (2-3 hours)
Pick ONE to prove the system works:
- CalDAV sync with Nextcloud/iCloud (3 hours)
- Todoist integration (2 hours)
- File monitoring (2 hours)

### Phase 4: Add Frontends (6-10 hours)
Once CRUD works:
- Telegram bot (2 hours)
- Simple web UI (4-6 hours)
- OpenWebUI function (2 hours)

## Frontend Interfaces (To Be Added After CRUD Works)

### 1. Telegram Bot
**When**: After Phase 2 (CRUD implemented)
**Where**: Create `telegram-bot/organizer_bot.py`
**How**: Copy from ai-ecosystem-integrated, connect to http://localhost:8002

Features:
- `/today` - Today's tasks and events
- `/todos` - Pending tasks
- `/events` - Upcoming calendar events
- Natural language: "Schedule meeting tomorrow at 3pm"

### 2. Simple Web GUI (Recommended: Streamlit)
**When**: After Phase 2
**Where**: Create `web-ui/app.py`
**How**: Streamlit is simpler than Gradio for forms

Features:
- Task management dashboard
- Calendar view
- Contact list
- Quick add forms

### 3. OpenWebUI Function
**When**: After Phase 2
**Where**: Create `openwebui/organizer_function.py`
**How**: Single file to drop into OpenWebUI

Features:
- `create_task(title, due_date, priority)`
- `get_my_tasks()`
- `get_my_events()`
- `ask_assistant(message)` - Natural language processing

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

**Current**: 4/10 - Server runs, no data persistence
**After CRUD**: 6/10 - Working API with data
**After 1 Integration**: 7/10 - Useful standalone tool
**After Frontends**: 8/10 - Production-ready for personal use

**Bottleneck**: CRUD implementation. Nothing else matters until this works.

## Recommended Work Order

1. **Week 1**: Implement CRUD (become 6/10)
2. **Week 1-2**: Add Todoist OR CalDAV sync (become 7/10)
3. **Week 2**: Add Telegram bot (test integration)
4. **Week 2-3**: Add web UI (polish user experience)
5. **Week 3**: Add OpenWebUI function (advanced usage)

Don't add frontends before CRUD works - you'll just have pretty interfaces showing empty data.
