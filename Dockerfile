FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create data directory for local storage
RUN mkdir -p /app/data

# Run the demo assistant by default
CMD ["python", "local_demo_assistant.py"]