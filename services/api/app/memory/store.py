import json
from uuid import UUID

from redis.asyncio import Redis

CALL_TTL_SECONDS = 24 * 60 * 60
SESSION_TTL_SECONDS = 60 * 60


class SessionMemoryStore:
    def __init__(self, redis: Redis | None = None) -> None:
        self.redis = redis

    async def save_active_session(self, session_id: UUID, payload: dict) -> None:
        if self.redis is None:
            return
        await self.redis.setex(
            self.session_key(session_id),
            SESSION_TTL_SECONDS,
            json.dumps(payload, default=str),
        )

    async def load_active_session(self, session_id: UUID) -> dict | None:
        if self.redis is None:
            return None
        raw = await self.redis.get(self.session_key(session_id))
        return json.loads(raw) if raw else None

    async def delete_active_session(self, session_id: UUID) -> None:
        if self.redis is None:
            return
        await self.redis.delete(self.session_key(session_id))

    async def start_call(
        self,
        *,
        call_id: UUID,
        session_id: UUID,
        tenant_id: UUID | None,
        direction: str,
        language: str,
        metadata: dict,
    ) -> None:
        if self.redis is None:
            return
        payload = {
            "call_id": str(call_id),
            "session_id": str(session_id),
            "tenant_id": str(tenant_id) if tenant_id else None,
            "direction": direction,
            "language": language,
            "metadata": metadata,
            "status": "active",
        }
        call_key = self.call_key(call_id)
        await self.redis.hset(call_key, mapping={"payload": json.dumps(payload, default=str)})
        await self.redis.expire(call_key, CALL_TTL_SECONDS)
        await self.redis.sadd("calls:active", str(call_id))
        await self.redis.setex(f"call_session:{call_id}", CALL_TTL_SECONDS, str(session_id))
        await self.save_active_session(
            session_id,
            {"call_id": call_id, "language": language, "state": "active", "history": []},
        )

    async def append_event(
        self,
        *,
        call_id: UUID | None,
        session_id: UUID | None,
        event_type: str,
        payload: dict,
        tenant_id: UUID | None = None,
    ) -> None:
        if self.redis is None or call_id is None:
            return
        item = {
            "tenant_id": str(tenant_id) if tenant_id else None,
            "call_id": str(call_id),
            "session_id": str(session_id) if session_id else None,
            "event_type": event_type,
            "payload": payload,
        }
        await self.redis.rpush(self.events_key(call_id), json.dumps(item, default=str))
        await self.redis.expire(self.events_key(call_id), CALL_TTL_SECONDS)

    async def append_transcript(
        self,
        *,
        call_id: UUID,
        session_id: UUID,
        speaker: str,
        text: str,
        language: str,
        confidence: float | None,
        metadata: dict,
        tenant_id: UUID | None = None,
    ) -> None:
        if self.redis is None:
            return
        item = {
            "tenant_id": str(tenant_id) if tenant_id else None,
            "call_id": str(call_id),
            "session_id": str(session_id),
            "speaker": speaker,
            "text": text,
            "language": language,
            "confidence": confidence,
            "metadata": metadata,
        }
        await self.redis.rpush(self.transcripts_key(call_id), json.dumps(item, default=str))
        await self.redis.expire(self.transcripts_key(call_id), CALL_TTL_SECONDS)

    async def finish_call(
        self,
        call_id: UUID,
        *,
        summary: str | None = None,
        action_items: dict | None = None,
    ) -> dict | None:
        if self.redis is None:
            return None
        call = await self.load_call(call_id)
        if call is None:
            return None
        call["status"] = "completed"
        if summary is not None:
            call["summary"] = summary
            call["action_items"] = action_items or {}
        await self.redis.hset(self.call_key(call_id), mapping={"payload": json.dumps(call, default=str)})
        await self.redis.srem("calls:active", str(call_id))
        return call

    async def load_call(self, call_id: UUID) -> dict | None:
        if self.redis is None:
            return None
        raw = await self.redis.hget(self.call_key(call_id), "payload")
        return json.loads(raw) if raw else None

    async def load_call_buffers(self, call_id: UUID) -> dict:
        if self.redis is None:
            return {"call": None, "events": [], "transcripts": []}
        call = await self.load_call(call_id)
        event_rows = await self.redis.lrange(self.events_key(call_id), 0, -1)
        transcript_rows = await self.redis.lrange(self.transcripts_key(call_id), 0, -1)
        return {
            "call": call,
            "events": [json.loads(row) for row in event_rows],
            "transcripts": [json.loads(row) for row in transcript_rows],
        }

    @staticmethod
    def session_key(session_id: UUID) -> str:
        return f"session:{session_id}"

    @staticmethod
    def call_key(call_id: UUID) -> str:
        return f"call:{call_id}"

    @staticmethod
    def events_key(call_id: UUID) -> str:
        return f"call:{call_id}:events"

    @staticmethod
    def transcripts_key(call_id: UUID) -> str:
        return f"call:{call_id}:transcripts"
