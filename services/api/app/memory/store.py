import json
from uuid import UUID

from redis.asyncio import Redis


class SessionMemoryStore:
    def __init__(self, redis: Redis | None = None) -> None:
        self.redis = redis

    async def save_active_session(self, session_id: UUID, payload: dict) -> None:
        if self.redis is None:
            return
        await self.redis.setex(f"session:{session_id}", 3600, json.dumps(payload, default=str))

    async def delete_active_session(self, session_id: UUID) -> None:
        if self.redis is None:
            return
        await self.redis.delete(f"session:{session_id}")
