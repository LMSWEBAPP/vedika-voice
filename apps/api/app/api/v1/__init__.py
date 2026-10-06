from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.leads import router as leads_router
from app.api.v1.calls import router as calls_router
from app.api.v1.agents import router as agents_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.appointments import router as appointments_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(campaigns_router)
api_v1_router.include_router(leads_router)
api_v1_router.include_router(calls_router)
api_v1_router.include_router(agents_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(webhooks_router)
api_v1_router.include_router(appointments_router)
