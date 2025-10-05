#!/usr/bin/env python3
"""
Telegram bot for Organizer Pipeline
Connects to organizer API at localhost:8000
"""

import os
import logging
from datetime import datetime, timedelta
import aiohttp
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ORGANIZER_SERVICE_URL = os.getenv("ORGANIZER_SERVICE_URL", "http://localhost:8000")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class OrganizerBot:
    """Telegram bot for task and calendar management"""

    def __init__(self):
        self.api_url = ORGANIZER_SERVICE_URL

    async def api_request(self, method: str, endpoint: str, data=None, params=None):
        """Make API request to organizer service"""
        url = f"{self.api_url}{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url, params=params) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        return None
                elif method == "POST":
                    async with session.post(url, json=data) as resp:
                        if resp.status in (200, 201):
                            return await resp.json()
                        return None
                elif method == "PUT":
                    async with session.put(url, json=data) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        return None
                elif method == "DELETE":
                    async with session.delete(url) as resp:
                        return resp.status == 204
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None

    async def get_tasks(self, status=None):
        """Get tasks from API"""
        params = {"status": status} if status else None
        return await self.api_request("GET", "/api/v1/tasks/", params=params)

    async def create_task(self, title, description="", priority="medium", due_date=None):
        """Create a new task"""
        data = {
            "title": title,
            "description": description,
            "priority": priority,
            "status": "pending"
        }
        if due_date:
            data["due_date"] = due_date.isoformat()

        return await self.api_request("POST", "/api/v1/tasks/", data=data)

    async def complete_task(self, task_id):
        """Mark task as completed"""
        data = {"status": "completed"}
        return await self.api_request("PUT", f"/api/v1/tasks/{task_id}", data=data)

    async def get_events(self):
        """Get upcoming calendar events"""
        return await self.api_request("GET", "/api/v1/calendar/events")

    async def create_event(self, title, start_time, end_time=None, description="", location=""):
        """Create calendar event"""
        if end_time is None:
            end_time = start_time + timedelta(hours=1)

        data = {
            "title": title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "description": description,
            "location": location
        }
        return await self.api_request("POST", "/api/v1/calendar/events", data=data)


bot = OrganizerBot()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    welcome = """
👋 Welcome to Personal Organizer Bot!

📋 **Task Commands:**
/todos - View pending tasks
/addtask [title] - Add a new task
/today - Today's tasks and events

📅 **Calendar Commands:**
/events - View upcoming events
/addevent [title] - Add a calendar event

💬 **Natural Language:**
Just type what you want to do:
- "Buy groceries due tomorrow"
- "Meeting with John at 3pm"
- "Reminder: Call mom"

Type /help for more info.
"""
    await update.message.reply_text(welcome)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    help_text = """
🤖 **Organizer Bot Help**

**Task Management:**
/todos - List all pending tasks
/addtask Title here - Quick task creation
/today - Today's overview

**Calendar:**
/events - Upcoming events
/addevent Event title - Quick event creation

**Natural Language Examples:**
✅ "Buy milk due tomorrow"
✅ "Team meeting Friday 2pm"
✅ "Call dentist priority high"
✅ "Remind me to exercise"

**Status:** Connected to {ORGANIZER_SERVICE_URL}
"""
    await update.message.reply_text(help_text)


async def todos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List pending tasks"""
    tasks = await bot.get_tasks(status="pending")

    if not tasks:
        await update.message.reply_text("📭 No pending tasks! You're all caught up.")
        return

    # Group by priority
    urgent = [t for t in tasks if t.get("priority") == "urgent"]
    high = [t for t in tasks if t.get("priority") == "high"]
    medium = [t for t in tasks if t.get("priority") == "medium"]
    low = [t for t in tasks if t.get("priority") == "low"]

    message = "📋 **Your Tasks:**\n\n"

    if urgent:
        message += "🔴 **URGENT:**\n"
        for task in urgent:
            message += f"• {task['title']}\n"
        message += "\n"

    if high:
        message += "🟠 **High Priority:**\n"
        for task in high:
            message += f"• {task['title']}\n"
        message += "\n"

    if medium:
        message += "🟡 **Medium Priority:**\n"
        for task in medium[:5]:  # Limit to 5
            message += f"• {task['title']}\n"
        if len(medium) > 5:
            message += f"... and {len(medium) - 5} more\n"
        message += "\n"

    if low:
        message += f"🟢 **Low Priority:** {len(low)} tasks\n"

    await update.message.reply_text(message, parse_mode='Markdown')


async def addtask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new task"""
    if not context.args:
        await update.message.reply_text("Usage: /addtask Your task title here")
        return

    title = " ".join(context.args)
    task = await bot.create_task(title)

    if task:
        await update.message.reply_text(f"✅ Task created: {title}")
    else:
        await update.message.reply_text("❌ Failed to create task")


async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List upcoming events"""
    events = await bot.get_events()

    if not events:
        await update.message.reply_text("📭 No upcoming events.")
        return

    message = "📅 **Upcoming Events:**\n\n"

    for event in events[:10]:  # Limit to 10
        start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
        title = event['title']
        location = event.get('location', '')

        message += f"• **{title}**\n"
        message += f"  {start.strftime('%Y-%m-%d %H:%M')}"
        if location:
            message += f" @ {location}"
        message += "\n\n"

    await update.message.reply_text(message, parse_mode='Markdown')


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show today's overview"""
    # Get today's tasks
    tasks = await bot.get_tasks(status="pending")

    # Get today's events
    events = await bot.get_events()

    now = datetime.now()
    today = now.date()

    # Filter events for today
    today_events = []
    if events:
        for event in events:
            start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
            if start.date() == today:
                today_events.append(event)

    message = f"📆 **Today: {today.strftime('%A, %B %d')}**\n\n"

    if today_events:
        message += "📅 **Events Today:**\n"
        for event in today_events:
            start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
            message += f"• {start.strftime('%H:%M')} - {event['title']}\n"
        message += "\n"

    if tasks:
        urgent = [t for t in tasks if t.get("priority") in ("urgent", "high")]
        if urgent:
            message += f"🔥 **Priority Tasks:** {len(urgent)} tasks\n"
            for task in urgent[:3]:
                message += f"• {task['title']}\n"
            if len(urgent) > 3:
                message += f"... and {len(urgent) - 3} more\n"
            message += "\n"

        message += f"📋 **Total Pending:** {len(tasks)} tasks\n"
    else:
        message += "✨ No pending tasks!\n"

    if not today_events and not tasks:
        message += "🌟 Free day! Enjoy!"

    await update.message.reply_text(message, parse_mode='Markdown')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle natural language messages"""
    text = update.message.text.lower()

    # Simple NLP for task creation
    if any(word in text for word in ["task", "todo", "remember", "remind"]):
        # Extract task title (simple approach)
        title = update.message.text

        # Determine priority
        priority = "medium"
        if "urgent" in text or "asap" in text:
            priority = "urgent"
        elif "important" in text or "high" in text:
            priority = "high"
        elif "low" in text:
            priority = "low"

        # Create task
        task = await bot.create_task(title, priority=priority)

        if task:
            await update.message.reply_text(f"✅ Task created: {title}\nPriority: {priority}")
        else:
            await update.message.reply_text("❌ Failed to create task")

    else:
        await update.message.reply_text(
            "I didn't understand that. Try:\n"
            "/todos - View tasks\n"
            "/addtask - Create a task\n"
            "/today - Today's overview"
        )


def main():
    """Start the bot"""
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN environment variable not set!")
        print("Get your token from @BotFather on Telegram")
        return

    # Create application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("todos", todos_command))
    app.add_handler(CommandHandler("addtask", addtask_command))
    app.add_handler(CommandHandler("events", events_command))
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start bot
    logger.info(f"Bot started! Connected to {ORGANIZER_SERVICE_URL}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
