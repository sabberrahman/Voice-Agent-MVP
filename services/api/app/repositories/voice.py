from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Call, CallEvent, CallSession, Summary, Tenant, Transcript

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


class VoiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_call_session(
        self,
        *,
        call_id: UUID,
        session_id: UUID,
        tenant_id: UUID | None,
        direction: str,
        language: str,
        metadata: dict,
    ) -> None:
        tenant_id = await self._resolve_tenant(tenant_id)
        call = await self.session.get(Call, call_id)
        if call is None:
            call = Call(
                id=call_id,
                tenant_id=tenant_id,
                direction=direction,
                status="active",
                started_at=datetime.now(UTC),
                metadata_json=metadata,
            )
            self.session.add(call)
        session = CallSession(
            id=session_id,
            call_id=call_id,
            tenant_id=tenant_id,
            state="active",
            language=language,
            context={},
        )
        self.session.add(session)
        await self.session.commit()

    async def ensure_call(
        self,
        *,
        call_id: UUID,
        tenant_id: UUID | None,
        direction: str = "inbound",
        language: str = "bn-BD",
    ) -> UUID:
        tenant_id = await self._resolve_tenant(tenant_id)
        call = await self.session.get(Call, call_id)
        if call is None:
            self.session.add(
                Call(
                    id=call_id,
                    tenant_id=tenant_id,
                    direction=direction,
                    status="active",
                    started_at=datetime.now(UTC),
                    metadata_json={"language": language},
                )
            )
            await self.session.commit()
        return tenant_id

    async def save_event(
        self,
        *,
        tenant_id: UUID | None,
        call_id: UUID | None,
        session_id: UUID | None,
        event_type: str,
        payload: dict,
    ) -> None:
        if call_id is None:
            return
        tenant_id = await self.ensure_call(call_id=call_id, tenant_id=tenant_id)
        self.session.add(
            CallEvent(
                tenant_id=tenant_id,
                call_id=call_id,
                session_id=session_id,
                event_type=event_type,
                payload=payload,
            )
        )
        await self.session.commit()

    async def save_transcript(
        self,
        *,
        tenant_id: UUID | None,
        call_id: UUID | None,
        session_id: UUID | None,
        speaker: str,
        text: str,
        language: str,
        confidence: float | None,
        metadata: dict,
    ) -> None:
        if call_id is None:
            return
        tenant_id = await self.ensure_call(
            call_id=call_id,
            tenant_id=tenant_id,
            language=language,
        )
        self.session.add(
            Transcript(
                tenant_id=tenant_id,
                call_id=call_id,
                session_id=session_id,
                speaker=speaker,
                text=text,
                language=language,
                confidence=int(confidence * 100) if confidence is not None else None,
            )
        )
        await self.save_event(
            tenant_id=tenant_id,
            call_id=call_id,
            session_id=session_id,
            event_type="transcript.saved",
            payload={"speaker": speaker, "language": language, "metadata": metadata},
        )

    async def save_summary(
        self,
        *,
        tenant_id: UUID | None,
        call_id: UUID,
        language: str,
        summary: str,
        action_items: dict,
    ) -> None:
        tenant_id = await self.ensure_call(call_id=call_id, tenant_id=tenant_id, language=language)
        self.session.add(
            Summary(
                tenant_id=tenant_id,
                call_id=call_id,
                language=language,
                summary=summary,
                action_items=action_items,
            )
        )
        call = await self.session.get(Call, call_id)
        if call is not None:
            call.status = "completed"
            call.ended_at = datetime.now(UTC)
        await self.session.commit()

    async def _resolve_tenant(self, tenant_id: UUID | None) -> UUID:
        tenant_id = tenant_id or DEFAULT_TENANT_ID
        tenant = await self.session.get(Tenant, tenant_id)
        if tenant is None:
            self.session.add(
                Tenant(
                    id=tenant_id,
                    name="Local Development Tenant",
                    slug="local-development",
                    locale="bn-BD",
                    is_active=True,
                    settings={},
                )
            )
            await self.session.flush()
        return tenant_id

    async def list_calls(self, *, limit: int = 50) -> list[Call]:
        result = await self.session.execute(select(Call).order_by(desc(Call.created_at)).limit(limit))
        return list(result.scalars().all())

    async def get_call(self, call_id: UUID) -> Call | None:
        return await self.session.get(Call, call_id)

    async def get_transcript(self, call_id: UUID) -> list[Transcript]:
        result = await self.session.execute(
            select(Transcript).where(Transcript.call_id == call_id).order_by(Transcript.created_at)
        )
        return list(result.scalars().all())

    async def get_summary(self, call_id: UUID) -> Summary | None:
        result = await self.session.execute(
            select(Summary).where(Summary.call_id == call_id).order_by(desc(Summary.created_at)).limit(1)
        )
        return result.scalar_one_or_none()
