"""
LLM service for processing natural language requests.
"""

import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from organizer_core.config import get_settings
from organizer_core.providers import create_llm_provider, BaseLLMProvider, LLMResponse
from organizer_core.providers.factory import get_available_providers
from organizer_core.models.calendar import CalendarEvent, EventType
from organizer_core.models.tasks import TodoItem, TaskPriority
from organizer_core.models.contacts import Contact

logger = logging.getLogger(__name__)


class LLMService:
    """Service for processing natural language requests with LLM."""

    def __init__(self):
        self.provider: Optional[BaseLLMProvider] = None
        self.settings = get_settings()

    async def initialize(self) -> None:
        """Initialize the LLM service with configured provider."""
        try:
            self.provider = create_llm_provider(
                self.settings.llm.provider,
                self.settings.llm.model_dump()
            )
            logger.info(f"LLM service initialized with {self.settings.llm.provider}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            # Fall back to demo provider
            self.provider = create_llm_provider("demo", {"model": "demo"})
            logger.info("Falling back to demo provider")

    async def process_user_input(self, user_input: str, system_prompt: str = "",
                               context: Dict[str, Any] = None) -> LLMResponse:
        """
        Process user input and return appropriate response.

        This method analyzes user input to determine intent and provides
        contextual responses for calendar, task, and contact management.
        """
        if not self.provider:
            raise RuntimeError("LLM service not initialized")

        context = context or {}

        # Create enhanced system prompt
        enhanced_system_prompt = self._create_system_prompt(system_prompt)

        # Process with provider
        response = await self.provider.generate_response(
            user_input,
            enhanced_system_prompt
        )

        # Analyze response for actionable items
        self._analyze_response_for_actions(user_input, response.content, context)

        return response

    def _create_system_prompt(self, additional_prompt: str = "") -> str:
        """Create comprehensive system prompt for the organizer assistant."""
        base_prompt = """You are a helpful personal organizer assistant. You can help users with:

📅 CALENDAR MANAGEMENT:
- Creating, updating, and managing calendar events
- Scheduling meetings and appointments
- Setting reminders and notifications
- Example: "Meeting with John tomorrow at 3pm in conference room A"

✅ TASK MANAGEMENT:
- Creating and organizing todo items
- Setting priorities and due dates
- Tracking task completion
- Example: "Remind me to call the bank next Friday, high priority"

📇 CONTACT MANAGEMENT:
- Adding and updating contact information
- Managing contact details and relationships
- Example: "Add Sarah Johnson, email sarah@company.com, phone 555-0123"

📊 INSIGHTS & SUMMARIES:
- Providing daily/weekly summaries
- Analyzing productivity patterns
- Suggesting optimizations

IMPORTANT GUIDELINES:
- Be concise and helpful
- Ask for clarification when needed
- Confirm actions before creating items
- Use natural, conversational language
- Respect user privacy and data security"""

        if additional_prompt:
            return f"{base_prompt}\n\nAdditional context: {additional_prompt}"

        return base_prompt

    def _analyze_response_for_actions(self, user_input: str, response: str,
                                    context: Dict[str, Any]) -> None:
        """
        Analyze the response to extract actionable items.

        This method identifies patterns in user input that suggest
        calendar events, tasks, or contacts should be created.
        """
        user_lower = user_input.lower()

        # Calendar event patterns
        calendar_patterns = [
            r'meeting.*(?:tomorrow|next week|on \w+day)',
            r'appointment.*(?:at \d+[:.]?\d*\s*(?:am|pm)?)',
            r'schedule.*(?:with|for)',
            r'(?:call|lunch|dinner).*(?:at|on|tomorrow)'
        ]

        # Task patterns
        task_patterns = [
            r'remind me.*(?:to|about)',
            r'todo.*',
            r'need to.*',
            r'don\'t forget.*'
        ]

        # Contact patterns
        contact_patterns = [
            r'add.*contact',
            r'save.*(?:email|phone)',
            r'add.*(?:email|phone).*(?:for|of)'
        ]

        actions_found = []

        for pattern in calendar_patterns:
            if re.search(pattern, user_lower):
                actions_found.append('calendar_event')
                break

        for pattern in task_patterns:
            if re.search(pattern, user_lower):
                actions_found.append('task')
                break

        for pattern in contact_patterns:
            if re.search(pattern, user_lower):
                actions_found.append('contact')
                break

        if actions_found:
            logger.info(f"Detected potential actions in user input: {actions_found}")
            context['suggested_actions'] = actions_found

    async def health_check(self) -> bool:
        """Check if the LLM service is healthy."""
        if not self.provider:
            return False

        try:
            return await self.provider.health_check()
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False

    def get_current_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider."""
        if not self.provider:
            return {"provider": "none", "status": "not_initialized"}

        return self.provider.get_info()

    def get_available_providers(self) -> Dict[str, str]:
        """Get list of available providers."""
        return get_available_providers()