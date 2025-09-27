#!/bin/bash
# Local Development Setup Script

set -e

echo "🔧 Setting up local development environment..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create data directory with proper permissions
echo "📁 Setting up data directory..."
rm -rf data 2>/dev/null || true
mkdir -p data
chmod 755 data

# Create config if it doesn't exist
if [ ! -f "enhanced_config.json" ]; then
    echo "⚙️ Creating default config..."
    cat > enhanced_config.json << 'EOF'
{
  "llm": {
    "provider": "demo",
    "model": "demo-model",
    "api_key": "demo-key",
    "base_url": "",
    "max_tokens": 2000
  },
  "caldav": {
    "url": "",
    "username": "",
    "password": ""
  },
  "carddav": {
    "url": "",
    "username": "",
    "password": ""
  },
  "monitoring": {
    "watch_directories": [
      "./test_watch"
    ],
    "file_extensions": [
      ".txt",
      ".md"
    ],
    "daily_summary_time": "18:00"
  },
  "preferences": {
    "default_calendar": "Personal",
    "default_event_duration": 60,
    "timezone": "UTC",
    "auto_categorize": true,
    "smart_suggestions": true
  },
  "integrations": {
    "email_enabled": false,
    "email_server": "",
    "web_interface": true,
    "api_enabled": true
  }
}
EOF
fi

echo "✅ Local development environment ready!"
echo ""
echo "🚀 To run the application:"
echo "   source .venv/bin/activate"
echo "   python enhanced_personal_assistant.py"
echo ""
echo "📋 Quick test commands:"
echo "   'Schedule meeting tomorrow at 3pm'"
echo "   'Add todo: finish project'"
echo "   '/help' for all commands"
echo "   'quit' to exit"