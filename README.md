## GROSINT AI Profiler

Asynchronous profiling backend service for social/content URLs with a comprehensive intelligence dashboard UI. Built with **FastAPI**, **Beanie/MongoDB**, **Celery**, and **React**.

### Features

- **Async profiling pipeline** (scrape → process → analyze)
- **Social/content sources**: Instagram, Facebook, Twitter/X, blogs/articles
- **Structured traits**: personality, work style, communication, risk, cultural fit, leadership
- **Job-based API**: create profile job, poll status, fetch details and raw data
- **Comprehensive Dashboard UI**:
  - Profile creation form for multiple platforms
  - Real-time status monitoring
  - Detailed profile analysis with visualizations
  - Network graphs and risk indicators
  - Activity timeline and raw data viewer
- **Structured logging** and simple API key auth

### Quick start (development)

1. Create and activate a Python 3.12 virtualenv.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set required environment variables (see `app/core/config.py` for full list), e.g.:

```bash
export APP_ENV=local
export MONGODB_URI="mongodb://localhost:27017/grosint_profiler"
export API_KEY="dev-secret-key"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/1"
```

4. Run the API:

```bash
uvicorn app.main:app --reload
```

5. Run Celery worker:

```bash
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

6. Run the frontend (in a separate terminal):

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Docker Setup

Run the entire stack with Docker Compose:

```bash
docker-compose up --build
```

This will start:
- MongoDB on port 27017
- Redis on port 6379
- API on port 8000
- Frontend on port 3000
- Celery worker

### Railway Deployment

This application is configured for deployment on Railway. See [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) for detailed deployment instructions.

**Quick Railway Setup:**
1. Create a Railway project and connect your GitHub repository
2. Add MongoDB and Redis services (Railway provides these as plugins)
3. Create two services: one for the API (web) and one for the Celery worker
4. Configure environment variables as documented in `RAILWAY_DEPLOYMENT.md`
5. Deploy!

The application includes:

- `Procfile` - Defines web and worker processes
- `railway.json` - Railway-specific configuration
- `.railwayignore` - Files to exclude from deployment
- `runtime.txt` - Python version specification

### Frontend Development

See `frontend/README.md` for detailed frontend setup and development instructions.

### Notes

- Scraping, ML, and LLM integrations are implemented via modular services with placeholder logic.
- External LLM API calls are **not** performed by default; integration hooks are provided for later wiring.
- The frontend uses mock data for the dashboard list view. In production, implement a profiles list endpoint.


change