# Local Development Guide

## Quick Start

```bash
# Setup (run once)
./local_dev.sh

# Run the application
./run_local.sh
```

That's it! Your development environment is ready.

## What Gets Set Up

1. **Virtual Environment**: Python dependencies isolated in `.venv/`
2. **Dependencies**: All packages from `requirements.txt` installed
3. **Data Directory**: Writable `data/` folder for storing events, todos, contacts
4. **Default Config**: Demo configuration in `enhanced_config.json`

## Local Development Workflow

### Daily Usage
```bash
# Start the assistant
./run_local.sh

# Example commands to try:
Schedule meeting tomorrow at 3pm with the team
Add todo: finish project documentation
/upcoming
/todos
/help
quit
```

### Development Tasks
```bash
# Activate environment for manual work
source .venv/bin/activate

# Run tests
python test_enhanced.py

# Direct script access
python enhanced_personal_assistant.py --help

# Install new dependencies
pip install some-package
pip freeze > requirements.txt
```

## File Structure
```
organizer-pipeline/
├── .venv/                    # Virtual environment (auto-created)
├── data/                     # Local data storage (auto-created)
│   ├── events.json          # Calendar events
│   ├── todos.json           # Todo items
│   └── contacts.json        # Contact information
├── enhanced_config.json     # Configuration (auto-created)
├── local_dev.sh            # Setup script
├── run_local.sh            # Quick run script
└── enhanced_personal_assistant.py  # Main application
```

## Configuration

Edit `enhanced_config.json` to customize:
- **LLM Provider**: Switch from demo to OpenAI/Anthropic/Ollama
- **CalDAV/CardDAV**: Add your server credentials
- **File Monitoring**: Set directories to watch
- **Timezone**: Change from UTC to your local timezone

## Troubleshooting

### Permission Issues
```bash
# Reset data directory
rm -rf data
mkdir data
chmod 755 data
```

### Dependencies Issues
```bash
# Recreate virtual environment
rm -rf .venv
./local_dev.sh
```

### Python Path Issues
```bash
# Always use the virtual environment
source .venv/bin/activate
which python  # Should show .venv/bin/python
```

## Comparison: Local vs Docker

| Aspect | Local Development | Docker |
|--------|-------------------|---------|
| **Setup** | `./local_dev.sh` | `docker build` |
| **Run** | `./run_local.sh` | `./run.sh` |
| **Data** | `./data/` | Volume mount |
| **Speed** | Faster startup | Slower startup |
| **Dependencies** | Uses system Python | Isolated container |
| **Debugging** | Native debugger | Container logs |

## Next Steps

1. **Configure Real LLM**: Replace demo provider with OpenAI/Claude API key
2. **Add CalDAV**: Connect to your calendar server (Nextcloud, iCloud, etc.)
3. **Customize**: Modify timezone, file monitoring, preferences
4. **Extend**: Add new features to the Python code

Your local development environment is now fully functional and easy to use!