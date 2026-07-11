from fastapi import APIRouter, Depends

from app.core.dependencies import get_provider_registry
from app.providers.factory import ProviderRegistry

router = APIRouter(tags=["providers"])


@router.get("/providers")
async def list_providers(registry: ProviderRegistry = Depends(get_provider_registry)) -> dict:
    return {"configured": registry.configured(), "available": registry.available()}
