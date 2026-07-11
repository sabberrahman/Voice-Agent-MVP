from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from redis.asyncio import Redis

from app.config.settings import get_settings

engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None
redis_client: Redis | None = None


async def init_database() -> None:
    global engine, SessionLocal, redis_client
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


async def close_database() -> None:
    if engine is not None:
        await engine.dispose()
    if redis_client is not None:
        await redis_client.aclose()


async def get_session() -> AsyncIterator[AsyncSession]:
    if SessionLocal is None:
        await init_database()
    assert SessionLocal is not None
    async with SessionLocal() as session:
        yield session


async def get_redis() -> Redis | None:
    return redis_client
