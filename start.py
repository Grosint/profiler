#!/usr/bin/env python3
"""Startup script for Railway deployment."""
import os
import sys
import subprocess
from pathlib import Path

# Add the current directory to Python path to ensure app module can be found
# This is critical for Railway where the working directory is /app
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Also set PYTHONPATH environment variable for subprocess
env = os.environ.copy()
pythonpath = env.get("PYTHONPATH", "")
if str(current_dir) not in pythonpath.split(os.pathsep):
    env["PYTHONPATH"] = f"{current_dir}{os.pathsep}{pythonpath}" if pythonpath else str(current_dir)

# Verify we can import the app module (helps with debugging)
try:
    import app
    print(f"✓ Successfully imported app module from {app.__file__}", file=sys.stderr)
except ImportError as e:
    print(f"✗ Failed to import app module: {e}", file=sys.stderr)
    print(f"  Current directory: {os.getcwd()}", file=sys.stderr)
    print(f"  Python path: {sys.path}", file=sys.stderr)
    print(f"  PYTHONPATH: {env.get('PYTHONPATH', 'not set')}", file=sys.stderr)
    sys.exit(1)

# Get PORT from environment or default to 8000
port = os.environ.get("PORT", "8000")

# Start uvicorn
cmd = [
    "uvicorn",
    "app.main:app",
    "--host", "0.0.0.0",
    "--port", str(port)
]

print(f"Starting uvicorn on port {port}...", file=sys.stderr)
sys.exit(subprocess.run(cmd, env=env).returncode)
