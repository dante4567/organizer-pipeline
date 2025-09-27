#!/usr/bin/env python3
"""
Test script for enhanced personal assistant with demo provider
"""

import asyncio
import sys
import os
sys.path.insert(0, '/app' if os.path.exists('/app') else '.')

from enhanced_personal_assistant import EnhancedPersonalAssistant

async def test_enhanced_assistant():
    print("🤖 Enhanced Personal Assistant Test")
    print("=" * 50)

    # Use demo config to avoid API requirements
    assistant = EnhancedPersonalAssistant("demo_config.json")

    test_commands = [
        "/help",
        "Meeting with Sarah tomorrow at 3pm in the conference room",
        "Remind me to call the bank next Tuesday",
        "Add John Doe to contacts, email john@company.com, phone +1234567890",
        "/upcoming",
        "/todos"
    ]

    print("🧪 Testing enhanced assistant with demo provider:")
    print("-" * 50)

    for cmd in test_commands:
        print(f"\nUser: {cmd}")
        try:
            response = await assistant.process_input(cmd)
            print(f"Assistant: {response}")
        except Exception as e:
            print(f"Error: {e}")

    print("\n✅ Enhanced assistant test completed!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_assistant())