#!/usr/bin/env python3
"""
Test script to demonstrate the local assistant functionality
"""

import sys
import os
sys.path.insert(0, '/app' if os.path.exists('/app') else '.')

from local_demo_assistant import LocalPersonalAssistant

def test_assistant():
    print("🤖 Local Demo Personal Assistant")
    print("=" * 50)
    print("This is a simplified demo version that:")
    print("✓ Works completely offline")
    print("✓ Uses simple pattern matching instead of LLM")
    print("✓ Saves everything to local JSON files")
    print("✓ No external dependencies required")
    print()

    assistant = LocalPersonalAssistant()

    # Test commands
    test_commands = [
        "Meeting with Sarah tomorrow at 3pm in the conference room",
        "Remind me to call the bank next Tuesday",
        "Add John Doe to contacts, email john@company.com, phone +1234567890",
        "/upcoming",
        "/todos",
        "/contacts"
    ]

    print("🧪 Testing assistant with sample commands:")
    print("-" * 40)

    for cmd in test_commands:
        print(f"\nUser: {cmd}")
        response = assistant.process_input(cmd)
        print(f"Assistant: {response}")

    print("\n✅ Test completed successfully!")
    print("\nGenerated files:")
    for file in ["local_events.json", "local_todos.json", "local_contacts.json"]:
        if os.path.exists(file):
            print(f"- {file}")

if __name__ == "__main__":
    test_assistant()