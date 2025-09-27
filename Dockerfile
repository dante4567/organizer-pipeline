FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory with world-writable permissions for cross-platform compatibility
RUN mkdir -p /app/data && chmod 777 /app/data

# Create volume for persistent data
VOLUME ["/app/data"]

# Expose port for future web interface
EXPOSE 8000

# Default command (can be overridden)
CMD ["python", "enhanced_personal_assistant.py"]
