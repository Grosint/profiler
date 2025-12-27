# Celery Debugging Commands

## 1. Check if Celery Worker Container is Running

```bash
# Check if worker container is running
docker-compose ps worker

# Check all containers
docker-compose ps

# Check worker container status and health
docker ps | grep worker
```

## 2. View Celery Worker Logs

```bash
# View real-time logs from worker container
docker-compose logs -f worker

# View last 100 lines of logs
docker-compose logs --tail=100 worker

# View logs with timestamps
docker-compose logs -f --timestamps worker

# View logs from last 10 minutes
docker-compose logs --since 10m worker
```

## 3. Check Redis Connection (Celery Broker)

```bash
# Check if Redis container is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check Redis keys (queued tasks)
docker-compose exec redis redis-cli KEYS "*"

# Monitor Redis commands in real-time
docker-compose exec redis redis-cli MONITOR

# Check Celery-specific keys
docker-compose exec redis redis-cli KEYS "celery*"
```

## 4. Check Celery Task Status

```bash
# Enter the worker container
docker-compose exec worker bash

# Inside the container, check Celery status
celery -A app.core.celery_app.celery_app inspect active

# Check registered tasks
celery -A app.core.celery_app.celery_app inspect registered

# Check scheduled tasks
celery -A app.core.celery_app.celery_app inspect scheduled

# Check reserved tasks (tasks that are being processed)
celery -A app.core.celery_app.celery_app inspect reserved

# Get worker stats
celery -A app.core.celery_app.celery_app inspect stats
```

## 5. Monitor Celery Events (Real-time)

```bash
# In one terminal, start event monitoring
docker-compose exec worker celery -A app.core.celery_app.celery_app events

# Or use flower for web-based monitoring (if installed)
# docker-compose exec worker celery -A app.core.celery_app.celery_app flower
```

## 6. Test Task Execution Manually

```bash
# Enter worker container
docker-compose exec worker bash

# Start Python shell
python

# In Python shell:
from app.tasks.post_tasks import run_post_analysis_pipeline
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings
import asyncio

# Test task directly (replace with actual post_id)
settings = get_settings()
client = AsyncIOMotorClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB_NAME]

# Initialize Beanie
await init_beanie(database=db, document_models=[...])  # Add your models

# Test the task
result = run_post_analysis_pipeline("YOUR_POST_ID_HERE")
print(result)
```

## 7. Check Task Results in Redis

```bash
# Check for task results
docker-compose exec redis redis-cli KEYS "celery-task-meta-*"

# Get a specific task result (replace TASK_ID)
docker-compose exec redis redis-cli GET "celery-task-meta-TASK_ID"
```

## 8. Restart Celery Worker

```bash
# Restart worker container
docker-compose restart worker

# Rebuild and restart worker
docker-compose up -d --build worker

# Stop and start worker
docker-compose stop worker
docker-compose start worker
```

## 9. Check API Logs (to see if tasks are being queued)

```bash
# View API container logs
docker-compose logs -f api

# Check for task dispatch messages
docker-compose logs api | grep "run_post_analysis_pipeline"
```

## 10. Verify Task Registration

```bash
# Enter worker container
docker-compose exec worker bash

# Check if post_tasks module is loaded
python -c "from app.tasks.post_tasks import run_post_analysis_pipeline; print('Task loaded:', run_post_analysis_pipeline)"

# List all registered tasks
celery -A app.core.celery_app.celery_app inspect registered | grep post
```

## 11. Check Database for Post Status

```bash
# Connect to MongoDB
docker-compose exec mongo mongosh grosint_profiler

# In MongoDB shell:
# Check posts collection
db.posts.find().pretty()

# Check a specific post
db.posts.findOne({_id: ObjectId("YOUR_POST_ID")})

# Check posts stuck in pending
db.posts.find({status: "pending"}).pretty()

# Check failed posts
db.posts.find({status: "failed"}).pretty()
```

## 12. Quick Health Check Script

Create a file `check_celery.sh`:

```bash
#!/bin/bash

echo "=== Checking Celery Worker ==="
docker-compose ps worker

echo -e "\n=== Checking Redis ==="
docker-compose exec redis redis-cli ping

echo -e "\n=== Checking Worker Status ==="
docker-compose exec worker celery -A app.core.celery_app.celery_app inspect active

echo -e "\n=== Recent Worker Logs ==="
docker-compose logs --tail=20 worker
```

Make it executable and run:
```bash
chmod +x check_celery.sh
./check_celery.sh
```

## Common Issues and Solutions

### Issue: Worker not running
```bash
# Check if worker container exists
docker-compose ps worker

# If not running, start it
docker-compose up -d worker

# Check logs for errors
docker-compose logs worker
```

### Issue: Tasks not being picked up
```bash
# Check if tasks are registered
docker-compose exec worker celery -A app.core.celery_app.celery_app inspect registered

# Check Redis connection
docker-compose exec redis redis-cli ping

# Restart worker
docker-compose restart worker
```

### Issue: Tasks failing silently
```bash
# Enable verbose logging
# Edit docker-compose.yml worker command to:
# command: ["celery", "-A", "app.core.celery_app.celery_app", "worker", "--loglevel=debug"]

# Then restart
docker-compose up -d --build worker

# Watch logs
docker-compose logs -f worker
```

## Monitoring Commands (Run in separate terminals)

Terminal 1 - Worker logs:
```bash
docker-compose logs -f worker
```

Terminal 2 - API logs:
```bash
docker-compose logs -f api
```

Terminal 3 - Redis monitor:
```bash
docker-compose exec redis redis-cli MONITOR
```
