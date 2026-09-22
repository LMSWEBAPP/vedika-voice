from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
    }


@router.get("/health/database")
async def health_database(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as exc:
        return {"status": "unhealthy", "error": "Database connection failed"}


@router.get("/health/redis")
async def health_redis():
    if settings.REDIS_URL:
        return {"status": "healthy", "redis": "configured"}
    return {"status": "healthy", "redis": "in-memory-fallback"}


@router.get("/health/ai")
async def health_ai():
    return {
        "status": "healthy",
        "provider": settings.AI_PROVIDER,
        "model": settings.GEMINI_MODEL,
        "configured": bool(settings.GEMINI_API_KEY) if settings.AI_PROVIDER == "gemini" else True,
    }


@router.get("/health/telephony")
async def health_telephony():
    return {
        "status": "healthy",
        "provider": settings.TELEPHONY_PROVIDER,
        "configured": bool(settings.EXOTEL_API_KEY) if settings.TELEPHONY_PROVIDER == "exotel" else True,
    }
