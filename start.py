#!/usr/bin/env python3
"""Startup script for Railway deployment."""
import os
import sys
import subprocess

# Get PORT from environment or default to 8000
port = os.environ.get("PORT", "8000")

# Start uvicorn
cmd = [
    "uvicorn",
    "app.main:app",
    "--host", "0.0.0.0",
    "--port", str(port)
]

sys.exit(subprocess.run(cmd).returncode)
