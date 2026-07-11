from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_redis, get_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/ready")
async def ready(session: AsyncSession = Depends(get_session), redis=Depends(get_redis)) -> dict:
    database = "ready"
    cache = "ready"
    try:
        await session.execute(text("select 1"))
    except Exception:  # noqa: BLE001
        database = "not_ready"
    if redis is not None:
        try:
            await redis.ping()
        except Exception:  # noqa: BLE001
            cache = "not_ready"
    status = "ready" if database == "ready" and cache == "ready" else "degraded"
    return {"status": status, "database": database, "redis": cache}
