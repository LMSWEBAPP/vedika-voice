# Veyra Voice — Deployment Guide

## Deployment Options

Veyra Voice can be deployed in two modes:

---

## 1. Zero-Dependency Local Development (Default)

Requires only Python 3.10+ and Node.js 18+. No Docker or external PostgreSQL/Redis setup needed:

```bash
# 1. Install and initialize backend
pip install -r apps/api/requirements.txt
python scripts/seed_database.py

# 2. Run backend API server
uvicorn apps.api.app.main:app --reload --port 8000

# 3. Run frontend dashboard
npm run dev:web
```

---

## 2. Containerized Production Deployment (Docker Compose)

For production staging on Render, Railway, Fly.io, or AWS EC2:

```bash
# Build and run Postgres, Redis, API, and Web containers
docker-compose up --build -d
```

### Production Environment Checklist
- `DATABASE_URL`: Set to production PostgreSQL (`postgresql+asyncpg://...`).
- `REDIS_URL`: Set to managed Redis instance (`redis://...`).
- `JWT_SECRET`: 64-character random hex string.
- `AI_PROVIDER`: Set to `gemini`.
- `GEMINI_API_KEY`: Injected from Google Cloud / AI Studio.
- `TELEPHONY_PROVIDER`: Set to `exotel`.
- `EXOTEL_ACCOUNT_SID` & `EXOTEL_API_KEY`: Carrier credentials.
- `TELEPHONY_WEBHOOK_BASE_URL`: Public HTTPS domain pointing to the FastAPI API.
