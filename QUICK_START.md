# Quick Start Guide - Personal Organizer

**Status**: 7/10 - CRUD works, frontends added, ready to use!

## What You Have

✅ **Backend API** - Tasks, calendar, contacts with full persistence
✅ **Telegram Bot** - Task management from your phone
✅ **Web UI** - Beautiful dashboard for planning

## 5-Minute Setup

### 1. Start the API Server
```bash
cd /Users/danielteckentrup/Documents/my-git/organizer-pipeline

# Option A: Direct command
cd src && \
SECURITY_SECRET_KEY="dev-secret-key-change-in-production-must-be-32-chars-min" \
LLM_PROVIDER="demo" \
LLM_MODEL="demo" \
DEBUG="true" \
python3 -m uvicorn organizer_api.main:app --host 127.0.0.1 --port 8000 --reload

# Option B: If you have a run script
./run_local.sh
```

**Test**: `curl http://localhost:8000/api/v1/tasks/` → Should return `[]`

### 2. Start the Web UI (New Terminal)
```bash
cd web-ui
pip install -r requirements.txt  # First time only
streamlit run app.py
```

**Access**: http://localhost:8501

### 3. Start Telegram Bot (Optional, New Terminal)
```bash
# Get token from @BotFather on Telegram first!
export TELEGRAM_BOT_TOKEN="your-token-from-botfather"

cd telegram-bot
pip install -r requirements.txt  # First time only
python organizer_bot.py
```

**Test**: Send `/start` to your bot

## First Steps

### Via Web UI (http://localhost:8501)
1. Click "📋 Tasks" in sidebar
2. Expand "➕ Create New Task"
3. Add your first task: "Test the organizer"
4. Click Create Task

### Via Telegram Bot
1. Message your bot: `/addtask Buy milk`
2. Check it worked: `/todos`
3. View today: `/today`

### Via API (curl)
```bash
# Create task
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title":"Learn API","priority":"high"}'

# View tasks
curl http://localhost:8000/api/v1/tasks/
```

## Daily Workflow

**Morning** (Telegram):
- `/today` - Check today's tasks and events

**Throughout Day** (Telegram):
- "Buy groceries due tomorrow"
- "Meeting with John at 3pm"

**Evening/Planning** (Web UI):
- Review all tasks
- Create calendar events for next week
- Organize by priority
- Add new contacts

## What Works

✅ Tasks CRUD - Create, read, update, delete, filter
✅ Calendar CRUD - Full event management
✅ Contacts CRUD - Full contact management
✅ Database persistence - Survives restarts
✅ Telegram interface - Phone access
✅ Web interface - Desktop dashboard

## What Doesn't Work (Yet)

❌ Authentication - No login, anyone with URL can access
❌ Multi-user - SQLite, single user only
❌ CalDAV sync - Can't sync with Apple Calendar/Google Calendar
❌ Real-time updates - Must refresh manually
❌ Task editing in Telegram - Delete and recreate instead

## Troubleshooting

### "Service is not running!" in Web UI
```bash
# Check API is running
curl http://localhost:8000/api/v1/tasks/

# If not, start it
cd src && python3 -m uvicorn organizer_api.main:app --host 127.0.0.1 --port 8000
```

### Telegram bot doesn't respond
```bash
# Check bot token is set
echo $TELEGRAM_BOT_TOKEN

# Check API is accessible
curl http://localhost:8000/api/v1/tasks/

# Check bot logs for errors
```

### Data disappeared after restart
```bash
# Check database exists
ls -la src/data/organizer.db

# If missing, database might have been created in wrong location
find . -name "organizer.db"
```

## Next Steps

**This Week**: Use it daily
- Add real tasks via Telegram
- Plan week in Web UI
- Add contacts as you meet people

**After 1 Week**: Assess
- What's annoying?
- What's missing?
- What broke?

**Then**: Fix top 3 pain points

## File Structure

```
organizer-pipeline/
├── src/                    # API backend
│   ├── organizer_api/     # FastAPI app
│   ├── organizer_core/    # Business logic
│   └── data/organizer.db  # SQLite database
├── telegram-bot/          # Telegram interface
│   ├── organizer_bot.py
│   └── requirements.txt
└── web-ui/                # Web dashboard
    ├── app.py
    └── requirements.txt
```

## URLs

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Web UI**: http://localhost:8501
- **Database**: `src/data/organizer.db`

## Support

Check the docs:
- `CLAUDE.md` - Current state, architecture
- `ADD_FRONTENDS_GUIDE.md` - Implementation details
- `IMPLEMENTATION_COMPLETE.md` - What was built

---

**You're ready to go! Start with the Web UI - it's the easiest way to see everything work.**
