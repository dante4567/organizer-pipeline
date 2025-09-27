# Advanced Personal Assistant Setup Guide

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure the assistant:**
Edit `assistant_config.json` with your settings:

### CalDAV/CardDAV Configuration
- **Nextcloud/ownCloud:** `https://your-server.com/remote.php/dav/`
- **Apple iCloud:** `https://caldav.icloud.com/` (requires app-specific password)
- **Google Calendar:** Not directly supported (use Nextcloud bridge or alternative)
- **Radicale (self-hosted):** `http://localhost:5232/your_user/`

### LLM Configuration

#### Option 1: OpenAI (Recommended for testing)
```json
"llm": {
  "provider": "openai",
  "model": "gpt-4",
  "api_key": "your_openai_api_key",
  "base_url": "https://api.openai.com/v1"
}
```

#### Option 2: Local Ollama (Privacy-focused)
```bash
# Install Ollama first
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama2  # or your preferred model
```

```json
"llm": {
  "provider": "ollama", 
  "model": "llama2",
  "api_key": "",
  "base_url": "http://localhost:11434"
}
```

## Usage

### Start the assistant:
```bash
python advanced_personal_assistant.py
```

### Natural Language Examples:
- "Meeting with Sarah tomorrow at 3pm in the conference room"
- "Remind me to call the bank next Tuesday"
- "Add John Doe to contacts, email john@company.com, phone +1234567890"
- "I have a dentist appointment this Friday at 10am"
- "Schedule a team standup every Monday at 9am"

### Commands:
- `/upcoming` - Show upcoming calendar events
- `/search John` - Search contacts for "John"  
- `/calendars` - List available calendars
- `/help` - Show all commands

## Server Configuration Examples

### Nextcloud
```json
"caldav": {
  "url": "https://nextcloud.example.com/remote.php/dav/",
  "username": "your_username",
  "password": "your_password"
},
"carddav": {
  "url": "https://nextcloud.example.com/remote.php/dav/",
  "username": "your_username", 
  "password": "your_password"
}
```

### Apple iCloud (CalDAV only)
```json
"caldav": {
  "url": "https://caldav.icloud.com/",
  "username": "your_apple_id@icloud.com",
  "password": "app_specific_password"
}
```
*Note: Generate app-specific password at appleid.apple.com*

### Self-hosted Radicale
```bash
# Install Radicale
pip install radicale
# Run server
python -m radicale --storage-filesystem-folder=~/.radicale/collections
```

```json
"caldav": {
  "url": "http://localhost:5232/your_username/",
  "username": "your_username",
  "password": "your_password"
}
```

## Features

### Calendar Management
- ✅ Create events from natural language
- ✅ Edit existing events  
- ✅ List upcoming events
- ✅ Support for multiple calendars
- ✅ Automatic datetime parsing
- ✅ Location and attendee support

### Todo Management  
- ✅ Create todos with due dates
- ✅ Priority levels (high/normal/low)
- ✅ Mark completed
- ✅ Persistent storage

### Contact Management
- ✅ Add contacts from conversation
- ✅ CardDAV sync
- ✅ Local fallback storage
- ✅ Search functionality
- ✅ Email and phone support

### LLM Integration
- ✅ Natural language processing
- ✅ Context-aware responses  
- ✅ Multiple LLM providers
- ✅ Local and cloud options

## Troubleshooting

### CalDAV Connection Issues
1. Verify server URL format
2. Check username/password
3. Test with a CalDAV client first
4. Check firewall/network settings

### LLM Issues  
1. Verify API key for cloud providers
2. Check Ollama is running for local setup
3. Test with simple queries first

### Contact Sync Issues
1. CardDAV might be separate from CalDAV
2. Check address book permissions
3. Fallback to local storage is automatic

### Permission Errors
```bash
# Make sure the script has write permissions
chmod +x advanced_personal_assistant.py
```

## Extending the Assistant

The assistant is designed to be modular. You can:

1. **Add new LLM providers** by extending the `call_llm()` method
2. **Add new calendar servers** by modifying connection logic  
3. **Add file monitoring** for automatic organization
4. **Create web/mobile frontends** using the core functions
5. **Add Telegram bot interface** using the same processing logic

## Security Notes

- Credentials are stored in plain text config file
- Consider using environment variables for production
- CalDAV/CardDAV traffic should use HTTPS
- Local LLM provides better privacy than cloud APIs

## Next Steps

1. Test with a simple setup first
2. Add your real calendar/contact data gradually  
3. Customize the LLM prompts for your needs
4. Add additional frontends (Telegram, web UI, etc.)
5. Integrate with file monitoring for daily summaries
