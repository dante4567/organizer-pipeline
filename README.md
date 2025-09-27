# organizer-pipeline

Advanced LLM-powered personal assistant for calendar, todo, and contact management with comprehensive CalDAV/CardDAV integration.

## 🚀 Quick Start

### Local Development (Recommended)
```bash
# Setup (run once)
./local_dev.sh

# Run the application
./run_local.sh
```

### Docker Alternative
```bash
# Build and run with Docker
docker build -t organizer-pipeline .
./run.sh

# Or use docker-compose for full setup
docker-compose up organizer-pipeline
```

## 🌟 Features

### Core Functionality
- 🧠 **Advanced LLM Integration** - Natural language processing with multiple providers
- 📅 **Smart Calendar Management** - Create, edit, recurring events with CalDAV sync
- ✅ **Intelligent Todo System** - Priority-based tasks with tags and due dates
- 📇 **Contact Management** - CardDAV sync with smart search
- 👁️ **File Monitoring** - Automatic file activity tracking and organization
- 📊 **Daily Summaries** - AI-generated insights and productivity reports

### LLM Providers Supported ✅ REAL AI INTEGRATION
- **Anthropic Claude** (Claude 3.5 Sonnet) - **Active & Configured**
- **OpenAI GPT** (GPT-4, GPT-3.5-turbo) - **API Key Available**
- **GROQ** (Llama 3.1 70B, Mixtral) - **Fast & Cost-Effective**
- **Local Ollama** (Llama 2, Mistral, CodeLlama, etc.) - **Optional**

### Integration Support ✅ CLOUD CONNECTED
- **CalDAV**: cloud.basurgis.de (Active), Nextcloud, ownCloud, Apple iCloud, Radicale
- **CardDAV**: Same as CalDAV plus dedicated contact servers
- **File Systems**: Real-time monitoring with intelligent categorization
- **Multiple Frontends**: Terminal, Web UI (planned), API, Telegram bot (planned)

## 📦 Installation Options

### Option 1: Docker (Easiest - Run Everywhere)

```bash
# Basic usage
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/enhanced_config.json:/app/enhanced_config.json:ro \
  organizer-pipeline

# With file monitoring
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/enhanced_config.json:/app/enhanced_config.json:ro \
  -v ~/Downloads:/app/watch/downloads:ro \
  -v ~/Documents:/app/watch/documents:ro \
  organizer-pipeline

# Full stack with local services
docker-compose --profile local-llm --profile local-caldav up
```

### Option 2: Native Python

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp enhanced_config.json my_config.json
# Edit my_config.json with your settings

# Run
python enhanced_personal_assistant.py
```

### Option 3: Container Interactive

```bash
# Run interactively in container
docker run -it --rm -p 8000:8000 organizer-pipeline python enhanced_personal_assistant.py
```

## ⚙️ Configuration

### LLM Configuration

#### OpenAI (Cloud)
```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "sk-...",
    "max_tokens": 2000
  }
}
```

#### Local Ollama (Privacy)
```bash
# Start Ollama
docker run -d -p 11434:11434 ollama/ollama
docker exec -it <container> ollama pull llama2
```

```json
{
  "llm": {
    "provider": "ollama",
    "model": "llama2",
    "base_url": "http://localhost:11434",
    "max_tokens": 2000
  }
}
```

#### Anthropic Claude
```json
{
  "llm": {
    "provider": "anthropic",
    "model": "claude-3-sonnet-20240229",
    "api_key": "sk-ant-...",
    "max_tokens": 2000
  }
}
```

### CalDAV/CardDAV Setup

#### Nextcloud/ownCloud
```json
{
  "caldav": {
    "url": "https://your-nextcloud.com/remote.php/dav/",
    "username": "your_username",
    "password": "your_password"
  },
  "carddav": {
    "url": "https://your-nextcloud.com/remote.php/dav/",
    "username": "your_username",
    "password": "your_password"
  }
}
```

#### Apple iCloud
```json
{
  "caldav": {
    "url": "https://caldav.icloud.com/",
    "username": "your_apple_id@icloud.com",
    "password": "app_specific_password"
  }
}
```

*Generate app-specific password at appleid.apple.com*

#### Local Radicale
```bash
# Start with docker-compose
docker-compose --profile local-caldav up radicale
```

```json
{
  "caldav": {
    "url": "http://localhost:5232/your_username/",
    "username": "your_username",
    "password": "your_password"
  }
}
```

## 🎯 Usage Examples

### Natural Language Processing

```bash
# Calendar events
"Meeting with Sarah tomorrow at 3pm in conference room B"
"Weekly standup every Monday at 9am"
"Lunch with team Friday at noon, recurring monthly"

# Todo management
"Remind me to call the bank next Tuesday, high priority"
"Buy groceries this weekend, low priority, tag: personal"
"Finish project report by Friday, tag: work, urgent"

# Contact management
"Add John Doe to contacts, email john@company.com, phone +1234567890, works at TechCorp"
"Save Sarah's info: sarah.smith@example.com, +1987654321"

# Information queries
"Show me meetings this week"
"What are my high priority tasks?"
"Find contacts at TechCorp"
```

### Commands

```bash
/upcoming          # Show upcoming events
/todos             # Show pending todos  
/search <query>    # Search contacts
/summary           # Generate daily summary
/stats             # Show statistics
/help              # Show all commands
```

## 🔧 Advanced Features

### File Monitoring
Automatically tracks file changes in specified directories:

```json
{
  "monitoring": {
    "watch_directories": ["~/Downloads", "~/Documents"],
    "file_extensions": [".pdf", ".doc", ".png"],
    "daily_summary_time": "18:00"
  }
}
```

### Recurring Events
Supports complex recurrence patterns:
- "Every Monday at 9am" → Weekly recurring
- "Monthly team meeting" → Monthly recurring
- "Daily standup at 9am" → Daily recurring

### Smart Prioritization
Todo items automatically sorted by:
1. Priority level (high → normal → low)
2. Due date (soonest first)
3. Creation date

### Daily Summaries
AI-generated daily insights including:
- Events attended
- Tasks completed
- File activities
- Productivity recommendations

## 🌐 API & Integrations

### REST API (Planned)
```bash
# Start with API enabled
python enhanced_personal_assistant.py --api

# Endpoints
POST /api/events      # Create event
GET /api/events       # List events
POST /api/todos       # Create todo
GET /api/contacts     # Search contacts
```

### Telegram Bot (Planned)
```bash
# Configure bot token
"integrations": {
  "telegram_bot_token": "your_bot_token"
}

# Use @your_bot_name in Telegram
```

## 📊 Data Storage

### Local Files
- `data/events.json` - Calendar events
- `data/todos.json` - Todo items
- `data/contacts.json` - Contact information
- `data/activities.json` - File activities
- `organizer_pipeline.log` - Application logs

### Cloud Sync
- CalDAV server for calendar events
- CardDAV server for contacts
- Local files as backup/cache

## 🔒 Security & Privacy

### Local-First
- All data stored locally by default
- Optional cloud sync via standard protocols
- No vendor lock-in

### LLM Privacy Options
- **Local Ollama**: Complete privacy, no data sent to cloud
- **OpenAI**: Encrypted API calls, follows OpenAI policies
- **Anthropic**: Encrypted API calls, follows Anthropic policies

### Data Protection
- CalDAV/CardDAV use standard authentication
- Passwords stored in config (consider environment variables)
- HTTPS for all external communications

## 🚀 Development

### Adding LLM Providers
```python
class CustomLLMProvider(LLMProvider):
    async def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        # Implement your provider
        pass
```

### Adding Integrations
```python
async def handle_custom_action(self, action: Dict):
    # Implement custom file actions, API calls, etc.
    pass
```

### Testing
```bash
# Run tests
python -m pytest tests/

# Test with demo data
python enhanced_personal_assistant.py --demo
```

## 📈 Roadmap

### v1.1 (Current)
- ✅ Enhanced LLM integration
- ✅ File monitoring
- ✅ Daily summaries
- ✅ Docker support

### v1.2 (Planned)
- 🔄 Web interface
- 🔄 REST API
- 🔄 Telegram bot
- 🔄 Email integration

### v1.3 (Future)
- 🔄 Mobile app
- 🔄 Voice interface
- 🔄 Advanced analytics
- 🔄 Team collaboration

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 Full documentation: [SETUP.md](SETUP.md)
- 🐛 Issues: [GitHub Issues](https://github.com/your-username/organizer-pipeline/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-username/organizer-pipeline/discussions)
- 📧 Email: your-email@example.com

## 🙏 Acknowledgments

- [python-caldav](https://github.com/python-caldav/caldav) for CalDAV integration
- [Ollama](https://ollama.ai) for local LLM hosting
- [OpenAI](https://openai.com) for GPT models
- [Anthropic](https://anthropic.com) for Claude models

---

**organizer-pipeline** - Your intelligent personal productivity companion 🤖✨
