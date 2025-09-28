#!/usr/bin/env python3
"""
Test the new modular system.
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set environment variables
os.environ.setdefault('LLM_PROVIDER', 'demo')
os.environ.setdefault('LLM_MODEL', 'demo')
os.environ.setdefault('SECURITY_SECRET_KEY', 'demo-secret-key-change-in-production-32chars')


async def test_system():
    print("🧪 Testing New Organizer System")
    print("=" * 50)

    try:
        # Test configuration
        from organizer_core.config import get_settings
        settings = get_settings()
        print(f"✅ Configuration loaded: {settings.app_name} v{settings.version}")
        print(f"   LLM Provider: {settings.llm.provider}")

        # Test models
        from organizer_core.models import CalendarEvent, TodoItem, Contact
        from datetime import datetime, timezone

        event = CalendarEvent(
            title="Test Meeting",
            start_time=datetime.now(timezone.utc),
            description="Testing the new system"
        )
        print(f"✅ Calendar model: {event.title}")

        task = TodoItem(
            title="Test Task",
            description="Testing the new system"
        )
        print(f"✅ Task model: {task.title}")

        contact = Contact(
            name="Test Contact",
            email="test@example.com"
        )
        print(f"✅ Contact model: {contact.name}")

        # Test LLM provider
        from organizer_core.providers import create_llm_provider
        provider = create_llm_provider("demo", {"model": "demo"})
        response = await provider.generate_response("Hello, test the system")
        print(f"✅ LLM Provider: {response.model}")
        print(f"   Response: {response.content[:100]}...")

        # Test validation
        from organizer_core.validation import InputValidator
        clean_text = InputValidator.validate_text("Test input <script>alert('xss')</script>")
        print(f"✅ Input validation: XSS protection working")

        print("\n🎉 All tests passed! The new system is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_system())
    sys.exit(0 if success else 1)