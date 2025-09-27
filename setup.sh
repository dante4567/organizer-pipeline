#!/bin/bash

# organizer-pipeline Setup Script
# Makes it easy to get started with the enhanced personal assistant

set -e

echo "🤖 organizer-pipeline Setup"
echo "============================"

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Docker found!"
    DOCKER_AVAILABLE=true
else
    echo "⚠️  Docker not found. Will use native Python setup."
    DOCKER_AVAILABLE=false
fi

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_AVAILABLE=true
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_AVAILABLE=true
    PYTHON_CMD=python
else
    echo "❌ Python not found. Please install Python 3.7+ first."
    exit 1
fi

echo ""
echo "🎯 Choose your setup option:"
echo "1) Docker (Recommended - runs everywhere)"
echo "2) Native Python (Local development)"
echo "3) Demo mode (No LLM/CalDAV, immediate testing)"

read -p "Enter choice (1-3): " choice

case $choice in
    1)
        if [ "$DOCKER_AVAILABLE" = false ]; then
            echo "❌ Docker not available. Please install Docker first."
            exit 1
        fi
        
        echo "🐳 Setting up Docker environment..."
        
        # Build the image
        echo "Building organizer-pipeline image..."
        docker build -t organizer-pipeline .
        
        # Create config if it doesn't exist
        if [ ! -f enhanced_config.json ]; then
            echo "📝 Creating default configuration..."
            cp enhanced_config.json enhanced_config.json.example
            echo "⚠️  Please edit enhanced_config.json with your LLM and CalDAV settings"
        fi
        
        echo ""
        echo "✅ Docker setup complete!"
        echo ""
        echo "🚀 To run:"
        echo "   docker run -it --rm -v \$(pwd)/data:/app/data -v \$(pwd)/enhanced_config.json:/app/enhanced_config.json:ro organizer-pipeline"
        echo ""
        echo "🔧 Or use docker-compose:"
        echo "   docker-compose up organizer-pipeline"
        
        ;;
        
    2)
        echo "🐍 Setting up native Python environment..."
        
        # Check pip
        if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
            echo "❌ pip not found. Please install pip first."
            exit 1
        fi
        
        # Install dependencies
        echo "📦 Installing dependencies..."
        if command -v pip3 &> /dev/null; then
            pip3 install -r requirements.txt
        else
            pip install -r requirements.txt
        fi
        
        # Create config if it doesn't exist
        if [ ! -f enhanced_config.json ]; then
            echo "📝 Creating default configuration..."
            echo "⚠️  Please edit enhanced_config.json with your LLM and CalDAV settings"
        fi
        
        echo ""
        echo "✅ Python setup complete!"
        echo ""
        echo "🚀 To run:"
        echo "   $PYTHON_CMD enhanced_personal_assistant.py"
        
        ;;
        
    3)
        echo "🎮 Setting up demo mode..."
        
        # Install minimal dependencies for demo
        echo "📦 Installing minimal dependencies..."
        if command -v pip3 &> /dev/null; then
            pip3 install python-dateutil
        else
            pip install python-dateutil
        fi
        
        echo ""
        echo "✅ Demo setup complete!"
        echo ""
        echo "🚀 To run demo:"
        echo "   $PYTHON_CMD local_demo_assistant.py"
        echo ""
        echo "🎯 Try these examples:"
        echo "   'Meeting with John tomorrow at 3pm'"
        echo "   'Remind me to call Sarah next week'"
        echo "   '/upcoming' to see your schedule"
        
        ;;
        
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "📚 Next steps:"
echo "1. Edit configuration files as needed"
echo "2. Run the assistant using the commands above"
echo "3. Type '/help' for available commands"
echo "4. Check README.md for full documentation"
echo ""
echo "🎉 Happy organizing!"
