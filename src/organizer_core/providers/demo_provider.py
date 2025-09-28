"""
Demo provider for testing without API keys.
"""

import asyncio
import random
from typing import Dict, Any

from .base import BaseLLMProvider, LLMResponse


class DemoProvider(BaseLLMProvider):
    """Demo provider that generates mock responses for testing."""

    def __init__(self, config: Dict[str, Any]):
        # Override config defaults for demo
        config.setdefault("model", "demo-model")
        config.setdefault("max_tokens", 2000)
        super().__init__(config)

    def get_required_config_fields(self) -> list[str]:
        """Demo provider has no required fields."""
        return []

    async def _make_request(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """Generate a mock response."""
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.1, 0.3))

        # Generate contextual responses based on prompt content
        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ["calendar", "event", "meeting", "schedule"]):
            responses = [
                "I've added the event to your calendar. The meeting is scheduled for the specified time.",
                "Calendar event created successfully. I'll remind you 15 minutes before the meeting.",
                "Your schedule has been updated with the new event. All attendees will be notified.",
                "Event added to your Personal calendar. Would you like to set any additional reminders?"
            ]
        elif any(word in prompt_lower for word in ["todo", "task", "remind", "reminder"]):
            responses = [
                "I've added this task to your todo list with the specified priority.",
                "Task created successfully. I'll remind you when the due date approaches.",
                "Your todo item has been saved. You can view all tasks using the /todos command.",
                "Reminder set! I'll make sure to notify you at the appropriate time."
            ]
        elif any(word in prompt_lower for word in ["contact", "person", "phone", "email"]):
            responses = [
                "Contact added successfully to your address book.",
                "I've saved the contact information. You can search for them anytime.",
                "Contact created with the provided details. Their information is now accessible.",
                "The person has been added to your contacts with all available information."
            ]
        elif any(word in prompt_lower for word in ["help", "commands", "what can"]):
            responses = [
                """I can help you with:
- 📅 Calendar management: "Meeting with John tomorrow at 3pm"
- ✅ Todo tasks: "Remind me to call the bank on Friday"
- 📇 Contacts: "Add Sarah's email sarah@company.com"
- 📊 Summaries: Use /summary for daily insights
- 🔍 Search: Use /search to find information

Just talk to me naturally!""",
            ]
        elif any(word in prompt_lower for word in ["upcoming", "schedule", "today", "tomorrow"]):
            responses = [
                "Here are your upcoming events: You have a team meeting at 2pm and a dentist appointment at 4pm.",
                "Your schedule looks light today - just one meeting at 3pm with the marketing team.",
                "You have 3 upcoming events this week. The next one is tomorrow at 10am.",
                "Today's agenda: Morning standup at 9am, lunch with clients at 12pm, project review at 3pm."
            ]
        elif any(word in prompt_lower for word in ["summary", "report", "overview"]):
            responses = [
                """📊 Daily Summary:
- ✅ Completed 3 tasks today
- 📅 2 meetings attended
- 📧 5 new contacts added
- 📈 Productivity: High

Key accomplishments: Project milestone reached, client presentation delivered successfully.""",
            ]
        else:
            # Generic helpful responses
            responses = [
                "I understand your request. I'm a demo version, but in the full system I would process this using AI.",
                "That's a great question! The production version would analyze this with advanced language models.",
                "I'd be happy to help with that. This demo shows how the system would respond to your input.",
                "Your request has been noted. The real system would use LLM providers to give you detailed assistance."
            ]

        content = random.choice(responses)

        return LLMResponse(
            content=content,
            model="demo-model-v1",
            tokens_used=len(content.split()) * 2,  # Rough token estimate
            finish_reason="stop",
            metadata={
                "demo_mode": True,
                "prompt_length": len(prompt),
                "response_type": "generated"
            }
        )