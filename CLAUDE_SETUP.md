# Claude API Setup Guide

## Getting Your Claude API Key

1. **Visit Anthropic Console**: Go to https://console.anthropic.com/
2. **Sign Up/Login**: Create an account or log in with existing credentials
3. **Create API Key**: Navigate to API Keys section and create a new key
4. **Copy the Key**: Copy the API key (starts with `sk-ant-api03-`)

## Configuration

### Option 1: Update Existing Config
Edit `enhanced_config.json`:

```json
{
  "llm": {
    "provider": "anthropic",
    "model": "claude-3-sonnet-20240229",
    "api_key": "sk-ant-api03-YOUR_ACTUAL_API_KEY_HERE",
    "base_url": "https://api.anthropic.com/v1/messages",
    "max_tokens": 2000
  }
}
```

### Option 2: Use Claude Test Config
Update `claude_test_config.json` with your API key and use it:

```bash
# Local testing
python enhanced_personal_assistant.py

# Docker testing
docker run -it --rm \
  -v $(pwd)/claude_test_config.json:/app/enhanced_config.json \
  -v $(pwd)/data:/app/data \
  organizer-pipeline
```

## Available Claude Models

- `claude-3-sonnet-20240229` (Recommended - balanced performance)
- `claude-3-haiku-20240307` (Faster, more cost-effective)
- `claude-3-opus-20240229` (Most capable, higher cost)

## Testing

Run the Claude-specific test:

```bash
# Update your API key in claude_test_config.json first
python test_claude.py

# Or with Docker
docker run --rm organizer-pipeline python test_claude.py
```

## Expected Behavior with Claude

Claude will provide much more sophisticated responses than the demo provider:

- **Smart Event Parsing**: Understands complex scheduling requests
- **Contextual Understanding**: Recognizes relationships between requests
- **Detailed Responses**: Provides helpful follow-up suggestions
- **Multi-item Processing**: Can handle multiple requests in one message

## API Costs

- Sonnet: ~$3 per million input tokens, ~$15 per million output tokens
- Typical usage: $0.01-0.10 per day for personal assistant tasks

## Troubleshooting

### 401 Unauthorized
- Check your API key is correct
- Ensure you have API access enabled
- Verify account has sufficient credits

### Rate Limits
- Free tier: Lower rate limits
- Paid tier: Higher limits
- Wait before retrying if hitting limits

### Network Issues
- Check internet connectivity
- Verify firewall allows HTTPS to api.anthropic.com
- Consider proxy settings if behind corporate firewall

## Security Notes

- Never commit API keys to version control
- Use environment variables for production
- Rotate keys regularly
- Monitor usage in Anthropic Console