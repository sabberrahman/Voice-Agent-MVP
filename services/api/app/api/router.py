from fastapi import APIRouter

from app.api.routes import admin, auth, calls, customers, dashboard, health, metrics, providers, transcripts, voice

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(admin.router)
api_router.include_router(providers.router)
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
api_router.include_router(calls.router, prefix="/calls", tags=["calls"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(transcripts.router, tags=["transcripts"])
api_router.include_router(metrics.router, tags=["metrics"])
api_router.include_router(dashboard.router, tags=["dashboard"])
