#!/bin/bash
# Quick run script for local development

echo "🚀 Starting organizer-pipeline locally..."

# Activate virtual environment
source .venv/bin/activate

# Run the application
python enhanced_personal_assistant.py "$@"