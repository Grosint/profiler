#!/usr/bin/env python3
"""Startup script for Railway deployment."""
import os
import sys
import subprocess
from pathlib import Path

# Get the root directory (where Procfile and start.py are located)
# On Railway, this is typically /app
root_dir = Path(__file__).parent.absolute()

# Set PYTHONPATH to the root directory so Python can find the 'app' package
# This is critical: if code is in /app/app/, then /app must be in PYTHONPATH
env = os.environ.copy()
pythonpath = env.get("PYTHONPATH", "")
if str(root_dir) not in pythonpath.split(os.pathsep):
    env["PYTHONPATH"] = f"{root_dir}{os.pathsep}{pythonpath}" if pythonpath else str(root_dir)

# Change working directory to root to ensure relative paths work
os.chdir(root_dir)

# Verify we can import the app module (helps with debugging)
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

# Get PORT from environment or default to 8000
port = os.environ.get("PORT", "8000")

# Start uvicorn with explicit PYTHONPATH in environment
# Use python -m uvicorn to ensure Python path is respected
cmd = [
    sys.executable,
    "-m", "uvicorn",
    "app.main:app",
    "--host", "0.0.0.0",
    "--port", str(port)
]

print(f"Starting uvicorn on port {port}...", file=sys.stderr)
print(f"  Command: {' '.join(cmd)}", file=sys.stderr)
print(f"  Working directory: {os.getcwd()}", file=sys.stderr)
print(f"  PYTHONPATH: {env.get('PYTHONPATH', 'not set')}", file=sys.stderr)
sys.exit(subprocess.run(cmd, env=env, cwd=root_dir).returncode)
