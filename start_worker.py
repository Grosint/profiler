#!/usr/bin/env python3
"""Startup script for Celery worker on Railway deployment."""
import os
import sys
from pathlib import Path

# Get the root directory (where Procfile and start_worker.py are located)
# On Railway, this is typically /app
root_dir = Path(__file__).parent.absolute()

# Set PYTHONPATH to the root directory so Python can find the 'app' package
env = os.environ.copy()
pythonpath = env.get("PYTHONPATH", "")
if str(root_dir) not in pythonpath.split(os.pathsep):
    env["PYTHONPATH"] = f"{root_dir}{os.pathsep}{pythonpath}" if pythonpath else str(root_dir)

# Change working directory to root
os.chdir(root_dir)

# Verify we can import the app module
try:
    # Add root to sys.path for this script's imports
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

    import app
    print(f"✓ Successfully imported app module from {app.__file__}", file=sys.stderr)
    print(f"  Working directory: {os.getcwd()}", file=sys.stderr)
    print(f"  PYTHONPATH: {env.get('PYTHONPATH', 'not set')}", file=sys.stderr)
except ImportError as e:
    print(f"✗ Failed to import app module: {e}", file=sys.stderr)
    print(f"  Current directory: {os.getcwd()}", file=sys.stderr)
    print(f"  Root directory: {root_dir}", file=sys.stderr)
    print(f"  Python path: {sys.path}", file=sys.stderr)
    print(f"  PYTHONPATH: {env.get('PYTHONPATH', 'not set')}", file=sys.stderr)
    sys.exit(1)

# Start celery worker
print("Starting Celery worker...", file=sys.stderr)
print(f"  Working directory: {os.getcwd()}", file=sys.stderr)
print(f"  PYTHONPATH: {env.get('PYTHONPATH', 'not set')}", file=sys.stderr)
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
