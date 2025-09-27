#!/usr/bin/env python3
"""
Test script for enhanced personal assistant with Claude API
"""

import asyncio
import sys
import os
import json
sys.path.insert(0, '/app' if os.path.exists('/app') else '.')

from enhanced_personal_assistant import EnhancedPersonalAssistant

async def test_claude_assistant():
    print("🤖 Enhanced Personal Assistant - Claude API Test")
    print("=" * 60)

    # Check if Claude API key is provided
    config_file = "claude_test_config.json"

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        api_key = config['llm']['api_key']
        if api_key == "sk-ant-api03-YOUR_CLAUDE_API_KEY_HERE":
            print("❌ Please set your Claude API key in claude_test_config.json")
            print("Replace 'sk-ant-api03-YOUR_CLAUDE_API_KEY_HERE' with your actual Claude API key")
            print("\nTo get a Claude API key:")
            print("1. Go to https://console.anthropic.com/")
            print("2. Sign up or log in")
            print("3. Create a new API key")
            print("4. Update the claude_test_config.json file")
            return

        print("✓ Claude API key found, initializing assistant...")
        assistant = EnhancedPersonalAssistant(config_file)

        test_commands = [
            "/help",
            "Schedule a team meeting tomorrow at 2pm in the conference room with John and Sarah",
            "Remind me to prepare the quarterly report by Friday, this is high priority",
            "Add Dr. Smith to my contacts, email dsmith@hospital.com, phone 555-0123, works at City Hospital",
            "I have a dentist appointment next Tuesday at 10:30am",
            "/upcoming",
            "/todos"
        ]

        print("🧪 Testing enhanced assistant with Claude API:")
        print("-" * 60)

        for cmd in test_commands:
            print(f"\nUser: {cmd}")
            try:
                response = await assistant.process_input(cmd)
                print(f"Assistant: {response}")
            except Exception as e:
                print(f"❌ Error: {e}")
                if "401" in str(e) or "unauthorized" in str(e).lower():
                    print("This might be an API key issue. Please check your Claude API key.")
                elif "rate" in str(e).lower() or "quota" in str(e).lower():
                    print("Rate limit or quota exceeded. Please wait before trying again.")

        print("\n✅ Claude API test completed!")
        print(f"\nGenerated files:")
        data_dir = assistant.data_dir
        for file in ["events.json", "todos.json", "contacts.json"]:
            filepath = data_dir / file
            if filepath.exists():
                print(f"- {filepath}")

    except FileNotFoundError:
        print(f"❌ Config file {config_file} not found")
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in {config_file}")
    except Exception as e:
        print(f"❌ Initialization error: {e}")

if __name__ == "__main__":
    asyncio.run(test_claude_assistant())