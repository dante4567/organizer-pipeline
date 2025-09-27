"""
OpenWebUI Integration Functions for Cloud Personal Data Service

Advanced integration with intelligent LLM routing, cost tracking, and
comprehensive personal data management capabilities.

Copy these functions into your OpenWebUI Functions section to integrate
with the Cloud Personal Data Management Service.
"""

def smart_manage_data(command: str):
    """
    Intelligent personal data management using advanced LLM processing.

    This function uses the cloud service's intelligent LLM routing to
    process complex natural language commands efficiently.

    Examples:
        - "Schedule a team meeting next Tuesday at 2pm in conference room A"
        - "Create a high priority task to review the quarterly budget by Friday"
        - "Add Sarah Johnson from TechCorp to my contacts with email sarah@techcorp.com"
        - "What's my schedule for tomorrow and what urgent tasks do I have?"
        - "Remind me to call the client about the proposal on Monday morning"
    """
    import requests

    try:
        response = requests.post(
            "http://localhost:8003/process/natural",
            json={"text": command},
            timeout=15
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Command processed successfully")
        else:
            return f"❌ Failed to process: {response.status_code} - {response.text}"
    except Exception as e:
        return f"❌ Error connecting to cloud personal data service: {str(e)}"

def intelligent_task_creation(description: str, priority: str = "medium", due_date: str = ""):
    """
    Create tasks with intelligent processing and context understanding.

    Uses advanced LLM models to understand context, extract metadata,
    and optimize task creation.

    Args:
        description: Natural language task description
        priority: low, medium, high, or urgent
        due_date: Natural language date (e.g., "next Friday", "in 3 days")
    """
    import requests

    try:
        # Use the smart parsing endpoint for enhanced task creation
        command = f"Create a {priority} priority task: {description}"
        if due_date:
            command += f" due {due_date}"

        response = requests.post(
            "http://localhost:8003/process/natural",
            json={"text": command},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return f"✅ {result.get('response', 'Task created successfully')}"
        else:
            return f"❌ Failed to create task: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_intelligent_daily_summary():
    """
    Get an AI-powered daily summary with insights and recommendations.

    Provides comprehensive analysis of your day including events, tasks,
    priorities, and intelligent suggestions.
    """
    import requests

    try:
        # Get comprehensive data
        events_response = requests.get("http://localhost:8003/calendar/today", timeout=10)
        tasks_response = requests.get("http://localhost:8003/tasks?status=pending&limit=10", timeout=10)
        stats_response = requests.get("http://localhost:8003/stats", timeout=10)

        summary = "🧠 **AI-Powered Daily Summary**\\n\\n"

        # Calendar Analysis
        if events_response.status_code == 200:
            events = events_response.json().get('events', [])
            if events:
                summary += "📅 **Today's Schedule:**\\n"
                for event in events:
                    start_time = event['start_time'][:16].replace('T', ' ')
                    summary += f"• {start_time}: **{event['title']}**"
                    if event.get('location'):
                        summary += f" @ {event['location']}"
                    summary += "\\n"
                summary += "\\n"
            else:
                summary += "📅 **Schedule**: Clear day - great for focused work!\\n\\n"

        # Intelligent Task Prioritization
        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get('tasks', [])
            urgent_tasks = [t for t in tasks if t.get('priority') == 'urgent']
            high_tasks = [t for t in tasks if t.get('priority') == 'high']

            if urgent_tasks:
                summary += "🚨 **Urgent Tasks** (Do First):\\n"
                for task in urgent_tasks[:3]:
                    summary += f"• **{task['title']}**"
                    if task.get('due_date'):
                        due_date = task['due_date'][:10]
                        summary += f" (Due: {due_date})"
                    summary += "\\n"
                summary += "\\n"

            if high_tasks:
                summary += "⚡ **High Priority Tasks**:\\n"
                for task in high_tasks[:3]:
                    summary += f"• {task['title']}"
                    if task.get('due_date'):
                        due_date = task['due_date'][:10]
                        summary += f" (Due: {due_date})"
                    summary += "\\n"
                summary += "\\n"

        # Performance Insights
        if stats_response.status_code == 200:
            stats = stats_response.json()
            summary += "📊 **Productivity Insights**:\\n"
            summary += f"• Total tasks: {stats.get('total_tasks', 0)} | Pending: {stats.get('pending_tasks', 0)}\\n"
            summary += f"• Calendar events today: {stats.get('today_events', 0)}\\n"
            summary += f"• Total contacts: {stats.get('total_contacts', 0)}\\n\\n"

        # AI Recommendations
        summary += "💡 **AI Recommendations**:\\n"
        if events_response.status_code == 200 and len(events) > 3:
            summary += "• Consider blocking focus time between meetings\\n"
        if tasks_response.status_code == 200 and len([t for t in tasks if t.get('priority') == 'urgent']) > 2:
            summary += "• You have multiple urgent tasks - consider delegating or rescheduling\\n"
        else:
            summary += "• Good balance of tasks and meetings today\\n"

        summary += "• Remember to take breaks between intense work sessions\\n"

        return summary

    except Exception as e:
        return f"❌ Error generating summary: {str(e)}"

def smart_contact_management(action: str, name: str = "", email: str = "", phone: str = "", company: str = ""):
    """
    Intelligent contact management with natural language processing.

    Args:
        action: "add", "search", or "update"
        name: Contact name
        email: Email address
        phone: Phone number
        company: Company name
    """
    import requests

    try:
        if action.lower() == "add":
            contact_data = {
                "name": name,
                "email": email if email else None,
                "phone": phone if phone else None,
                "company": company if company else None
            }

            response = requests.post(
                "http://localhost:8003/contacts",
                json=contact_data,
                timeout=10
            )

            if response.status_code == 200:
                contact_id = response.json().get("contact_id")
                return f"📇 Contact added: **{name}** (ID: {contact_id})"
            else:
                return f"❌ Failed to add contact: {response.status_code}"

        elif action.lower() == "search":
            query = name or email or company
            response = requests.get(
                f"http://localhost:8003/contacts?search={query}",
                timeout=10
            )

            if response.status_code == 200:
                contacts = response.json().get('contacts', [])
                if contacts:
                    result = f"📇 Found {len(contacts)} contact(s):\\n"
                    for contact in contacts[:5]:
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

        else:
            return "❌ Action must be 'add' or 'search'"

    except Exception as e:
        return f"❌ Error: {str(e)}"

def smart_schedule_event(title: str, datetime_description: str, duration: str = "1 hour", location: str = ""):
    """
    Intelligent event scheduling with natural language date/time parsing.

    Uses advanced LLM models to understand complex date/time expressions.

    Args:
        title: Event title
        datetime_description: Natural language date/time (e.g., "next Tuesday at 2pm", "tomorrow morning")
        duration: Duration description (e.g., "1 hour", "30 minutes", "2.5 hours")
        location: Event location
    """
    import requests

    try:
        command = f"Schedule '{title}' {datetime_description}"
        if duration != "1 hour":
            command += f" for {duration}"
        if location:
            command += f" at {location}"

        response = requests.post(
            "http://localhost:8003/process/natural",
            json={"text": command},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return f"📅 {result.get('response', 'Event scheduled successfully')}"
        else:
            return f"❌ Failed to schedule event: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_cost_analytics():
    """
    Get comprehensive cost analytics for LLM usage.

    Provides detailed breakdown of costs by provider, operation type,
    and usage patterns for budget management.
    """
    import requests

    try:
        response = requests.get("http://localhost:8003/analytics/costs", timeout=10)

        if response.status_code == 200:
            costs = response.json()

            result = "💰 **LLM Cost Analytics**\\n\\n"
            result += f"**Total Costs**: ${costs.get('total', 0):.3f}\\n\\n"

            # By provider
            if 'by_provider' in costs:
                result += "**By Provider**:\\n"
                for provider, cost in costs['by_provider'].items():
                    result += f"• {provider.title()}: ${cost:.3f}\\n"
                result += "\\n"

            # By operation
            if 'by_operation' in costs:
                result += "**By Operation Type**:\\n"
                for operation, cost in costs['by_operation'].items():
                    result += f"• {operation.replace('_', ' ').title()}: ${cost:.3f}\\n"
                result += "\\n"

            # Daily summary
            daily_response = requests.get("http://localhost:8003/analytics/costs/daily", timeout=5)
            if daily_response.status_code == 200:
                daily = daily_response.json()
                result += f"**Today**: ${daily.get('total_cost', 0):.3f} ({daily.get('requests', 0)} requests)\\n"
                result += f"**Avg per request**: ${daily.get('average_cost_per_request', 0):.4f}\\n"

            return result
        else:
            return f"❌ Failed to get cost analytics: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def check_cloud_service_health():
    """
    Comprehensive health check for the cloud personal data service.

    Checks all service components including LLM providers, database,
    scheduler, and provides detailed status information.
    """
    import requests

    try:
        response = requests.get("http://localhost:8003/health", timeout=10)

        if response.status_code == 200:
            health = response.json()
            status = health.get('status', 'unknown')
            services = health.get('services', {})

            if status == 'healthy':
                result = "🟢 **Service Status**: All systems operational\\n\\n"
            elif status == 'degraded':
                result = "🟡 **Service Status**: Some issues detected\\n\\n"
            else:
                result = "🔴 **Service Status**: Service issues\\n\\n"

            result += "**Component Status**:\\n"
            result += f"• Database: {services.get('database', 'unknown')}\\n"
            result += f"• LLM Services: {services.get('llm', 'unknown')}\\n"
            result += f"• Background Scheduler: {services.get('scheduler', 'unknown')}\\n"
            result += f"• File System: {services.get('files', 'unknown')}\\n\\n"

            # LLM provider status
            if 'llm_providers' in health:
                result += "**LLM Provider Status**:\\n"
                for provider, status in health['llm_providers'].items():
                    icon = "🟢" if status == "available" else "🔴"
                    result += f"• {icon} {provider.title()}: {status}\\n"

            return result
        else:
            return f"❌ Service health check failed: {response.status_code}"
    except Exception as e:
        return f"❌ Service not available: {str(e)}"

def quick_productivity_snapshot():
    """
    Get a quick productivity snapshot with key metrics and insights.

    Combines calendar, tasks, and usage analytics for a high-level overview.
    """
    import requests

    try:
        stats_response = requests.get("http://localhost:8003/stats", timeout=5)
        costs_response = requests.get("http://localhost:8003/analytics/costs/daily", timeout=5)

        result = "⚡ **Productivity Snapshot**\\n\\n"

        if stats_response.status_code == 200:
            stats = stats_response.json()

            # Key metrics
            result += f"📊 **Today**: {stats.get('today_events', 0)} events, {stats.get('pending_tasks', 0)} pending tasks\\n"
            result += f"📈 **Total**: {stats.get('total_tasks', 0)} tasks, {stats.get('total_contacts', 0)} contacts\\n\\n"

            # Quick insights
            pending_ratio = stats.get('pending_tasks', 0) / max(stats.get('total_tasks', 1), 1)
            if pending_ratio > 0.7:
                result += "⚠️ **Alert**: High ratio of pending tasks - consider prioritizing\\n"
            elif pending_ratio < 0.3:
                result += "✅ **Great**: Most tasks completed - good productivity!\\n"
            else:
                result += "📊 **Status**: Balanced task completion rate\\n"

        if costs_response.status_code == 200:
            costs = costs_response.json()
            result += f"💰 **AI Usage**: ${costs.get('total_cost', 0):.3f} today ({costs.get('requests', 0)} requests)\\n"

        return result

    except Exception as e:
        return f"❌ Error getting snapshot: {str(e)}"

def parse_complex_intent(text: str):
    """
    Parse complex user intentions using advanced LLM models.

    Uses intelligent model routing to understand user intent and extract
    structured information from natural language.

    Args:
        text: Natural language text to parse
    """
    import requests

    try:
        response = requests.post(
            "http://localhost:8003/llm/parse-intent",
            json={"text": text},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()

            output = f"🧠 **Intent Analysis**\\n\\n"
            output += f"**Intent**: {result.get('intent', 'unknown')}\\n"
            output += f"**Confidence**: {result.get('confidence', 0):.1%}\\n\\n"

            if 'entities' in result and result['entities']:
                output += "**Extracted Information**:\\n"
                for key, value in result['entities'].items():
                    output += f"• {key.title()}: {value}\\n"
                output += "\\n"

            if 'reasoning' in result:
                output += f"**Analysis**: {result['reasoning']}\\n"

            return output
        else:
            return f"❌ Failed to parse intent: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def sync_todoist_tasks():
    """
    Sync all Todoist tasks to the local database.

    Fetches all tasks from Todoist and stores them locally with metadata
    for unified task management across platforms.
    """
    import requests

    try:
        response = requests.post(
            "http://localhost:8003/todoist/sync",
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            sync_data = result['result']

            output = f"🔄 **Todoist Sync Complete**\\n\\n"
            output += f"✅ **Synced**: {sync_data['synced_tasks']} new tasks\\n"
            output += f"📊 **Total**: {sync_data['total_todoist_tasks']} Todoist tasks\\n"
            output += f"⏰ **Completed**: {sync_data['timestamp'][:19].replace('T', ' ')}\\n\\n"

            if sync_data['synced_tasks'] > 0:
                output += f"💡 **Tip**: Use `get_intelligent_daily_summary()` to see your updated task overview\\n"

            return output
        else:
            return f"❌ Sync failed: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_todoist_projects():
    """
    Get all Todoist projects with summary information.

    Retrieves the complete list of your Todoist projects for better
    organization and project-specific task management.
    """
    import requests

    try:
        response = requests.get(
            "http://localhost:8003/todoist/projects",
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            projects = result['projects']

            output = f"📁 **Todoist Projects** ({len(projects)} total)\\n\\n"

            # Show favorites first
            favorites = [p for p in projects if p.get('is_favorite')]
            if favorites:
                output += "⭐ **Favorites**:\\n"
                for project in favorites[:5]:
                    output += f"• **{project['name']}** ({project['color']})\\n"
                output += "\\n"

            # Show inbox
            inbox = [p for p in projects if p.get('is_inbox_project')]
            if inbox:
                output += "📥 **Inbox**:\\n"
                for project in inbox:
                    output += f"• **{project['name']}**\\n"
                output += "\\n"

            # Show recent projects (first 10)
            output += "📋 **All Projects** (showing first 10):\\n"
            for project in projects[:10]:
                name = project['name']
                if len(name) > 30:
                    name = name[:27] + "..."
                output += f"• {name}\\n"

            if len(projects) > 10:
                output += f"\\n... and {len(projects) - 10} more projects\\n"

            return output
        else:
            return f"❌ Failed to get projects: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def create_todoist_task(content: str, priority: str = "medium", project_name: str = ""):
    """
    Create a new task in Todoist with intelligent priority mapping.

    Args:
        content: Task description
        priority: low, medium, high, or urgent
        project_name: Optional project name (searches for best match)
    """
    import requests

    try:
        # Map priority to Todoist scale (1-4)
        priority_map = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "urgent": 4
        }
        todoist_priority = priority_map.get(priority.lower(), 2)

        task_data = {
            "content": content,
            "priority": todoist_priority
        }

        # If project specified, try to find it
        if project_name:
            projects_response = requests.get("http://localhost:8003/todoist/projects", timeout=5)
            if projects_response.status_code == 200:
                projects = projects_response.json()['projects']
                # Simple search for matching project
                for project in projects:
                    if project_name.lower() in project['name'].lower():
                        task_data["project_id"] = project['id']
                        break

        response = requests.post(
            "http://localhost:8003/todoist/tasks",
            json=task_data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            task = result['task']

            output = f"✅ **Todoist Task Created**\\n\\n"
            output += f"📝 **Title**: {task['content']}\\n"
            output += f"⚡ **Priority**: {priority} (level {todoist_priority})\\n"
            output += f"🆔 **ID**: {task['id']}\\n"

            if task.get('project_id'):
                output += f"📁 **Project**: {task['project_id']}\\n"

            output += f"🔗 **Link**: {task['url']}\\n"

            return output
        else:
            return f"❌ Failed to create task: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"