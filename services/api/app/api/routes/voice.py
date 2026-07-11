from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_provider_registry, get_voice_orchestrator
from app.db.session import get_session
from app.providers.factory import ProviderRegistry
from app.repositories.voice import VoiceRepository
from app.schemas.voice import (
    ProviderSelectionRequest,
    VoiceEndRequest,
    VoiceEventRequest,
    VoiceSessionResponse,
    VoiceStartRequest,
)
from app.voice.orchestrator import VoiceOrchestrator

router = APIRouter()


@router.post("/start", response_model=VoiceSessionResponse)
async def start_voice(
    payload: VoiceStartRequest,
    orchestrator: VoiceOrchestrator = Depends(get_voice_orchestrator),
    session: AsyncSession = Depends(get_session),
) -> VoiceSessionResponse:
    return await orchestrator.start(payload, repository=VoiceRepository(session))


@router.post("/audio")
async def process_voice_audio(
    call_id: Annotated[UUID, Form()],
    session_id: Annotated[UUID, Form()],
    language: Annotated[str, Form()] = "bn-BD",
    tenant_id: Annotated[UUID | None, Form()] = None,
    audio: UploadFile = File(...),
    orchestrator: VoiceOrchestrator = Depends(get_voice_orchestrator),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    audio_bytes = await audio.read()
    result, audio_response = await orchestrator.process_audio(
        call_id=call_id,
        session_id=session_id,
        tenant_id=tenant_id,
        language=language,
        audio=audio_bytes,
        repository=VoiceRepository(session),
    )
    headers = {
        "x-call-id": str(result.call_id),
        "x-session-id": str(result.session_id),
        "x-transcript": result.transcript.encode("utf-8").hex(),
        "x-response-text": result.response_text.encode("utf-8").hex(),
        "x-latencies-ms": result.model_dump_json(include={"latencies_ms"}),
    }
    return StreamingResponse(iter([audio_response]), media_type=result.audio_mime_type, headers=headers)


@router.post("/end", response_model=VoiceSessionResponse)
async def end_voice(
    payload: VoiceEndRequest,
    x_tenant_id: UUID | None = Header(default=None),
    orchestrator: VoiceOrchestrator = Depends(get_voice_orchestrator),
    session: AsyncSession = Depends(get_session),
) -> VoiceSessionResponse:
    return await orchestrator.end(payload, repository=VoiceRepository(session), tenant_id=x_tenant_id)


@router.post("/event", response_model=VoiceSessionResponse)
async def voice_event(
    payload: VoiceEventRequest,
    x_tenant_id: UUID | None = Header(default=None),
    orchestrator: VoiceOrchestrator = Depends(get_voice_orchestrator),
    session: AsyncSession = Depends(get_session),
) -> VoiceSessionResponse:
    await VoiceRepository(session).save_event(
        tenant_id=x_tenant_id,
        call_id=payload.call_id,
        session_id=payload.session_id,
        event_type=payload.event_type,
        payload=payload.payload,
    )
    return await orchestrator.event(payload)


@router.post("/provider")
async def select_provider(
    payload: ProviderSelectionRequest,
    registry: ProviderRegistry = Depends(get_provider_registry),
) -> dict:
    requested = payload.model_dump(exclude_none=True)
    return {"status": "accepted", "requested": requested, "active": registry.configured()}
