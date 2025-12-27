# Frontend Setup Guide

## Fixing "Unauthorized" Error

The "Unauthorized" error occurs when the API key is not properly configured. Here's how to fix it:

### For Local Development

1. **Create a `.env` file** in the `frontend` directory:

```bash
cd frontend
cp .env.example .env
```

2. **Edit `.env`** and set your API key:

```bash
VITE_API_BASE_URL=/api/v1
VITE_API_KEY=dev-secret-key
```

3. **Restart the dev server**:

```bash
npm run dev
```

### For Docker

The API key is now passed during build time. If you need to change it:

1. **Update `docker-compose.yml`**:

```yaml
frontend:
  build:
    context: ./frontend
    args:
      VITE_API_BASE_URL: /api/v1
      VITE_API_KEY: "your-api-key-here"  # Match the API_KEY in the api service
```

2. **Rebuild the frontend**:

```bash
docker-compose build frontend
docker-compose up frontend
```

### Verify API Key Match

Make sure the API key in your frontend matches the API key in your backend:

- **Backend** (docker-compose.yml): `API_KEY: "dev-secret-key"`
- **Frontend** (.env or docker-compose.yml): `VITE_API_KEY: "dev-secret-key"`

They must match exactly!

### Quick Test

After setting up, check the browser console (F12). You should see:
```
API Base URL: /api/v1
API Key configured: dev-secre...
```

If you see "NOT SET", the API key is missing.
