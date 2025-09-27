#!/bin/bash
# Convenience script to run organizer-pipeline

# Create data directory if it doesn't exist
mkdir -p ./data

echo "🚀 Starting organizer-pipeline..."
echo "📁 Data will be saved to: $(pwd)/data"

# Run Docker container with volume mounts
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/enhanced_config.json:/app/enhanced_config.json:ro \
  organizer-pipeline "$@"