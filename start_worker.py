#!/usr/bin/env python3
"""Startup script for Celery worker on Railway deployment."""
import os
import sys
from pathlib import Path

# Add the current directory to Python path to ensure app module can be found
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Set PYTHONPATH environment variable
env = os.environ.copy()
pythonpath = env.get("PYTHONPATH", "")
if str(current_dir) not in pythonpath.split(os.pathsep):
    env["PYTHONPATH"] = f"{current_dir}{os.pathsep}{pythonpath}" if pythonpath else str(current_dir)

# Verify we can import the app module
try:
    import app
    print(f"✓ Successfully imported app module from {app.__file__}", file=sys.stderr)
except ImportError as e:
    print(f"✗ Failed to import app module: {e}", file=sys.stderr)
    print(f"  Current directory: {os.getcwd()}", file=sys.stderr)
    print(f"  Python path: {sys.path}", file=sys.stderr)
    print(f"  PYTHONPATH: {env.get('PYTHONPATH', 'not set')}", file=sys.stderr)
    sys.exit(1)

# Start celery worker
print("Starting Celery worker...", file=sys.stderr)
os.execve(
    sys.executable,
    [
        sys.executable,
        "-m", "celery",
        "-A", "app.core.celery_app.celery_app",
        "worker",
        "--loglevel=info"
    ],
    env
)
