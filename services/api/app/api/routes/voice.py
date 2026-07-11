import base64
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
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
    VoiceSpeakRequest,
    VoiceSessionResponse,
    VoiceStartRequest,
)
from app.voice.orchestrator import VoiceOrchestrator

router = APIRouter()


@router.post("/start", response_model=VoiceSessionResponse)
async def start_voice(
    payload: VoiceStartRequest,
    orchestrator: VoiceOrchestrator = Depends(get_voice_orchestrator),
) -> VoiceSessionResponse:
    return await orchestrator.start(payload)


@router.post("/audio")
async def process_voice_audio(
    call_id: Annotated[UUID, Form()],
    session_id: Annotated[UUID, Form()],
    language: Annotated[str, Form()] = "bn-BD",
    tenant_id: Annotated[UUID | None, Form()] = None,
    audio: UploadFile = File(...),
    orchestrator: VoiceOrchestrator = Depends(get_voice_orchestrator),
) -> StreamingResponse:
    audio_bytes = await audio.read()
    result, audio_response = await orchestrator.process_audio(
        call_id=call_id,
        session_id=session_id,
        tenant_id=tenant_id,
        language=language,
        audio=audio_bytes,
    )
    headers = {
        "x-call-id": str(result.call_id),
        "x-session-id": str(result.session_id),
        "x-transcript": result.transcript.encode("utf-8").hex(),
        "x-response-text": result.response_text.encode("utf-8").hex(),
        "x-latencies-ms": result.model_dump_json(include={"latencies_ms"}),
    }
    return StreamingResponse(iter([audio_response]), media_type=result.audio_mime_type, headers=headers)


@router.post("/speak")
async def speak_voice_text(
    payload: VoiceSpeakRequest,
    orchestrator: VoiceOrchestrator = Depends(get_voice_orchestrator),
) -> StreamingResponse:
    result, audio_response = await orchestrator.synthesize_text(
        call_id=payload.call_id,
        session_id=payload.session_id,
        tenant_id=payload.tenant_id,
        language=payload.language,
        text=payload.text,
    )
    headers = {
        "x-call-id": str(result.call_id),
        "x-session-id": str(result.session_id),
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
    orchestrator: VoiceOrchestrator = Depends(get_voice_orchestrator),
) -> VoiceSessionResponse:
    return await orchestrator.event(payload)


@router.websocket("/ws")
async def voice_websocket(
    websocket: WebSocket,
    orchestrator: VoiceOrchestrator = Depends(get_voice_orchestrator),
) -> None:
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_json()
            message_type = message.get("type")
            if message_type == "start":
                payload = VoiceStartRequest.model_validate(message.get("payload") or {})
                response = await orchestrator.start(payload)
                await websocket.send_json(
                    {"type": "started", "payload": response.model_dump(mode="json")}
                )
            elif message_type == "audio":
                payload = message.get("payload") or {}
                call_id = UUID(payload["call_id"])
                session_id = UUID(payload["session_id"])
                audio = base64.b64decode(payload.get("audio_b64") or "")
                result, audio_response = await orchestrator.process_audio(
                    call_id=call_id,
                    session_id=session_id,
                    tenant_id=UUID(payload["tenant_id"]) if payload.get("tenant_id") else None,
                    language=payload.get("language") or "bn-BD",
                    audio=audio,
                )
                await websocket.send_json(
                    {
                        "type": "audio_result",
                        "payload": {
                            **result.model_dump(mode="json"),
                            "audio_b64": base64.b64encode(audio_response).decode("ascii"),
                        },
                    }
                )
            elif message_type == "speak":
                payload = message.get("payload") or {}
                call_id = UUID(payload["call_id"])
                session_id = UUID(payload["session_id"])
                result, audio_response = await orchestrator.synthesize_text(
                    call_id=call_id,
                    session_id=session_id,
                    tenant_id=UUID(payload["tenant_id"]) if payload.get("tenant_id") else None,
                    language=payload.get("language") or "bn-BD",
                    text=payload["text"],
                )
                await websocket.send_json(
                    {
                        "type": "audio_result",
                        "payload": {
                            **result.model_dump(mode="json"),
                            "audio_b64": base64.b64encode(audio_response).decode("ascii"),
                        },
                    }
                )
            elif message_type == "event":
                payload = VoiceEventRequest.model_validate(message.get("payload") or {})
                response = await orchestrator.event(payload)
                await websocket.send_json(
                    {"type": "event_received", "payload": response.model_dump(mode="json")}
                )
            elif message_type == "end":
                payload = VoiceEndRequest.model_validate(message.get("payload") or {})
                response: VoiceSessionResponse | None = None
                async for db_session in get_session():
                    response = await orchestrator.end(
                        payload,
                        repository=VoiceRepository(db_session),
                    )
                    break
                if response is None:
                    await websocket.send_json({"type": "error", "message": "Database is unavailable"})
                    continue
                await websocket.send_json(
                    {"type": "ended", "payload": response.model_dump(mode="json")}
                )
            elif message_type == "ping":
                await websocket.send_json(
                    {"type": "pong", "request_id": message.get("request_id") or str(uuid4())}
                )
            else:
                await websocket.send_json(
                    {"type": "error", "message": f"Unsupported message type: {message_type}"}
                )
    except WebSocketDisconnect:
        return


@router.post("/provider")
async def select_provider(
    payload: ProviderSelectionRequest,
    registry: ProviderRegistry = Depends(get_provider_registry),
) -> dict:
    requested = payload.model_dump(exclude_none=True)
    return {"status": "accepted", "requested": requested, "active": registry.configured()}
