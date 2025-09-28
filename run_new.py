#!/usr/bin/env python3
"""
Run the new secure organizer API.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set environment variables for demo
os.environ.setdefault('LLM_PROVIDER', 'demo')
os.environ.setdefault('LLM_MODEL', 'demo')
os.environ.setdefault('SECURITY_SECRET_KEY', 'demo-secret-key-change-in-production-32chars')
os.environ.setdefault('DEBUG', 'true')

if __name__ == "__main__":
    from organizer_api.main import run_server
    run_server()