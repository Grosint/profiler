# Railway Deployment Fix - Manual Dashboard Configuration

## Critical Issue
If you're still seeing the error: `The executable 'pythonpath=/app:$pythonpath' could not be found`

This means Railway has a **manually configured start command** in the dashboard that's overriding your Procfile.

## Solution: Update Railway Dashboard Settings

### For API Service:
1. Go to your Railway project dashboard
2. Click on your **API Service** (the main web service)
3. Go to **Settings** → **Deploy** (or **Settings** → **Start Command**)
4. **Clear any existing start command** or set it to:
   ```
   python start.py
   ```
5. Make sure there's NO `PYTHONPATH=/app:$PYTHONPATH` in the command
6. Save the changes

### For Worker Service:
1. Go to your Railway project dashboard
2. Click on your **Worker Service** (the Celery worker service)
3. Go to **Settings** → **Deploy** (or **Settings** → **Start Command**)
4. **Clear any existing start command** or set it to:
   ```
   python start_worker.py
   ```
5. Make sure there's NO `PYTHONPATH=/app:$PYTHONPATH` in the command
6. Save the changes

## Alternative: Use Procfile Detection

If Railway supports Procfile detection:
1. In each service's Settings → Deploy
2. Look for a **"Process Type"** or **"Use Procfile"** option
3. Select **"web"** for API service
4. Select **"worker"** for Worker service
5. This will automatically use the commands from your Procfile

## Verify Your Procfile

Your Procfile should contain (and nothing else):
```
web: python start.py
worker: python start_worker.py
```

**DO NOT** include environment variable assignments like `PYTHONPATH=/app:$PYTHONPATH` in the Procfile - Railway's Nixpacks builder doesn't parse them correctly.

## After Making Changes

1. **Redeploy** your services (Railway should auto-deploy, or trigger a manual redeploy)
2. Check the deployment logs to verify the correct command is being used
3. The error should be resolved
