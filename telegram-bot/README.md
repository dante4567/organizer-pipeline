# Telegram Bot for Personal Organizer

Quick task and calendar management from your phone.

## Setup

### 1. Install Dependencies
```bash
cd telegram-bot
pip install -r requirements.txt
```

### 2. Get Bot Token
1. Message `@BotFather` on Telegram
2. Send `/newbot`
3. Follow prompts to create your bot
4. Copy the token you receive

### 3. Configure
```bash
export TELEGRAM_BOT_TOKEN="your-token-here"
export ORGANIZER_SERVICE_URL="http://localhost:8000"  # Optional, defaults to this
```

### 4. Run
```bash
# Make sure organizer service is running first!
# In another terminal: cd ../src && ./run_local.sh

python organizer_bot.py
```

## Features

### Commands
- `/start` - Welcome message
- `/help` - Show help
- `/todos` - List pending tasks
- `/addtask [title]` - Quick task creation
- `/events` - View upcoming events
- `/today` - Today's overview

### Natural Language
Just type what you want:
- "Buy milk due tomorrow"
- "Team meeting Friday 2pm"
- "Call dentist priority high"
- "Remind me to exercise"

## Usage Examples

```
You: /addtask Buy groceries
Bot: ✅ Task created: Buy groceries

You: /todos
Bot: 📋 Your Tasks:
     🟡 Medium Priority:
     • Buy groceries

You: Create task: Call dentist priority high
Bot: ✅ Task created: Create task: Call dentist priority high
     Priority: high

You: /today
Bot: 📆 Today: Sunday, October 05
     🔥 Priority Tasks: 1 tasks
     • Call dentist
     📋 Total Pending: 2 tasks
```

## Troubleshooting

**Bot doesn't respond:**
- Check organizer service is running at localhost:8000
- Check `TELEGRAM_BOT_TOKEN` is set correctly
- Check bot logs for errors

**"Failed to create task":**
- Verify organizer API is accessible: `curl http://localhost:8000/api/v1/tasks/`
- Check API server logs

## Limits

- No authentication (anyone with bot token can access)
- Simple NLP (keyword-based task creation)
- No task editing via bot (use Web UI)
