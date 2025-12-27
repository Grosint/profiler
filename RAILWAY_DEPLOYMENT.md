# Railway Deployment Guide

This guide will help you deploy the GROSINT AI Profiler application to Railway.

## Prerequisites

1. A Railway account (sign up at [railway.app](https://railway.app))
2. Railway CLI installed (optional, but recommended): `npm i -g @railway/cli`

## Deployment Steps

### 1. Create a New Project on Railway

1. Go to [railway.app](https://railway.app) and create a new project
2. Click "New Project" → "Deploy from GitHub repo" (or use Railway CLI)

### 2. Add Required Services

You'll need to add the following services to your Railway project:

#### A. MongoDB Database
1. Click "New" → "Database" → "MongoDB"
2. Railway will automatically provision a MongoDB instance
3. Note the connection string from the MongoDB service variables

#### B. Redis Database
1. Click "New" → "Database" → "Redis"
2. Railway will automatically provision a Redis instance
3. Note the connection string from the Redis service variables

#### C. API Service (Main Application)
1. Click "New" → "GitHub Repo" (or "Empty Service" if using CLI)
2. Select your repository
3. Railway will auto-detect it as a Python application

#### D. Worker Service (Celery)
1. Click "New" → "GitHub Repo" (or clone the API service)
2. Select the same repository
3. Configure it to run as a worker (see configuration below)

### 3. Configure Environment Variables

For the **API Service**, set the following environment variables:

```bash
# App Configuration
APP_ENV=production
DEBUG=0
API_KEY=your-secure-api-key-here
API_V1_PREFIX=/api/v1

# MongoDB (use Railway's MongoDB connection string)
MONGODB_URI=${{MongoDB.MONGO_URL}}
MONGODB_DB_NAME=grosint_profiler

# Redis (use Railway's Redis connection string)
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}

# CORS (adjust based on your frontend domain)
CORS_ALLOW_ORIGINS=https://your-frontend-domain.railway.app,https://your-custom-domain.com
CORS_ALLOW_CREDENTIALS=true

# Logging
LOG_LEVEL=INFO
LOG_JSON=1
```

For the **Worker Service**, set the same environment variables as the API service.

**Note:** Railway automatically provides `${{ServiceName.VARIABLE_NAME}}` syntax to reference variables from other services. Use:
- `${{MongoDB.MONGO_URL}}` for MongoDB connection
- `${{Redis.REDIS_URL}}` for Redis connection

### 4. Configure Service Settings

#### API Service Settings:
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Railway will automatically use the PORT environment variable

#### Worker Service Settings:
- **Start Command:** `celery -A app.core.celery_app.celery_app worker --loglevel=info`
- Or use the Procfile: Railway will detect the `worker` process type

### 5. Deploy Frontend (Optional)

You have two options for the frontend:

#### Option A: Deploy as Separate Service
1. Create a new service for the frontend
2. Set build command: `cd frontend && npm ci && npm run build`
3. Set start command: `cd frontend && npx serve -s dist -l $PORT`
4. Configure environment variables:
   - `VITE_API_BASE_URL=/api/v1` (or your API URL)
   - `VITE_API_KEY=your-api-key`

#### Option B: Serve from API (Recommended for simplicity)
1. Build the frontend locally: `cd frontend && npm run build`
2. Copy the `dist` folder to the root or configure FastAPI to serve static files
3. Add static file serving to your FastAPI app

### 6. Configure Domains

1. Go to each service → Settings → Generate Domain
2. Railway will provide a `.railway.app` domain
3. For custom domains, add them in Settings → Domains

### 7. Deploy

Railway will automatically deploy when you push to your connected branch. You can also:
- Use Railway Dashboard to trigger manual deployments
- Use Railway CLI: `railway up`

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `API_KEY` | Yes | API key for authentication | `your-secure-key` |
| `MONGODB_URI` | Yes | MongoDB connection string | `mongodb://...` |
| `MONGODB_DB_NAME` | No | Database name | `grosint_profiler` |
| `CELERY_BROKER_URL` | Yes | Redis broker URL | `redis://...` |
| `CELERY_RESULT_BACKEND` | Yes | Redis result backend | `redis://...` |
| `APP_ENV` | No | Environment name | `production` |
| `DEBUG` | No | Debug mode | `0` or `1` |
| `CORS_ALLOW_ORIGINS` | No | Allowed CORS origins | `https://example.com` |
| `LOG_LEVEL` | No | Logging level | `INFO` |
| `LOG_JSON` | No | Use JSON logging | `1` |

## Railway-Specific Features

### Automatic Port Binding
Railway automatically sets the `PORT` environment variable. The Procfile uses `${PORT:-8000}` to handle this.

### Service Dependencies
Railway automatically waits for dependent services (MongoDB, Redis) to be ready before starting your application.

### Health Checks
Railway will check your `/api/v1/health` endpoint. Make sure it returns a 200 status.

### Resource Limits
- Free tier: 512MB RAM, $5 credit/month
- Pro tier: More resources available
- Consider upgrading if you need more memory for ML models

## Troubleshooting

### Build Failures
- Check build logs in Railway dashboard
- Ensure all dependencies in `requirements.txt` are compatible
- Playwright installation may take time - be patient

### Connection Issues
- Verify MongoDB and Redis connection strings are correct
- Check that services are in the same Railway project
- Ensure environment variables are set correctly

### Worker Not Processing Tasks
- Verify worker service is running
- Check that `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` are set
- Check worker logs in Railway dashboard

### Memory Issues
- ML models can be memory-intensive
- Consider upgrading Railway plan
- Monitor memory usage in Railway dashboard

## Monitoring

Railway provides:
- Real-time logs for all services
- Metrics dashboard (CPU, Memory, Network)
- Deployment history
- Service health status

## Cost Considerations

- MongoDB: Included in Railway pricing
- Redis: Included in Railway pricing
- Compute: Based on usage (free tier available)
- Bandwidth: Included in most plans

## Security Notes

1. **Never commit API keys** - Use Railway environment variables
2. **Use strong API keys** - Generate secure random strings
3. **Enable HTTPS** - Railway provides this automatically
4. **Review CORS settings** - Only allow trusted origins
5. **Monitor logs** - Check for suspicious activity

## Support

- Railway Docs: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Railway Status: [status.railway.app](https://status.railway.app)
