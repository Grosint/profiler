#!/usr/bin/env python3
"""Startup script for Railway deployment."""
import os
import sys
from pathlib import Path

# Get the root directory (where Procfile and start.py are located)
# On Railway, this is typically /app
root_dir = Path(__file__).parent.absolute()

# CRITICAL: Add root directory to Python path FIRST, before any imports
# This ensures all subsequent imports can find the 'app' package
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Change working directory to root
os.chdir(root_dir)

# Set PYTHONPATH environment variable for any subprocesses
os.environ["PYTHONPATH"] = str(root_dir)

print(f"Root directory: {root_dir}", file=sys.stderr)
print(f"Working directory: {os.getcwd()}", file=sys.stderr)
print(f"Python path: {sys.path[:3]}...", file=sys.stderr)
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'not set')}", file=sys.stderr)

# Verify we can import the app module and its submodules
try:
    import app
    print(f"✓ Successfully imported app module from {app.__file__}", file=sys.stderr)

    # Test importing the problematic module
    from app.models import profile
    print(f"✓ Successfully imported app.models.profile from {profile.__file__}", file=sys.stderr)

    # Test importing the main app
    from app.main import app as fastapi_app
    print(f"✓ Successfully imported app.main.app", file=sys.stderr)
except ImportError as e:
    print(f"✗ Failed to import: {e}", file=sys.stderr)
    print(f"  Current directory: {os.getcwd()}", file=sys.stderr)
    print(f"  Root directory: {root_dir}", file=sys.stderr)
    print(f"  Python path: {sys.path}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# Get PORT from environment or default to 8000
port = int(os.environ.get("PORT", "8000"))

# Import and run uvicorn programmatically
# This ensures we're using the same Python interpreter and path
try:
    import uvicorn
    print(f"Starting uvicorn on port {port}...", file=sys.stderr)
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
except Exception as e:
    print(f"✗ Failed to start uvicorn: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
