import asyncio
import base64
import json
import os
import wave
from io import BytesIO
from uuid import UUID

import httpx
import websockets
from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
API_WS_URL = os.getenv(
    "API_WS_URL",
    API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://"),
)
FREESWITCH_ESL_HOST = os.getenv("FREESWITCH_ESL_HOST", "freeswitch")
FREESWITCH_ESL_PORT = int(os.getenv("FREESWITCH_ESL_PORT", "8021"))
FREESWITCH_EVENT_SOCKET_PASSWORD = os.getenv("FREESWITCH_EVENT_SOCKET_PASSWORD", "ClueCon")
DOGRAH_MEDIA_CHUNK_MS = int(os.getenv("DOGRAH_MEDIA_CHUNK_MS", "1200"))
PCM_8K_BYTES_PER_MS = 16

app = FastAPI(
    title="VoxAgent Dograh Bridge",
    version="0.1.0",
    description="Routes call session events to the Voice Orchestrator. No STT, TTS or LLM logic lives here.",
)


class DograhSessionEvent(BaseModel):
    call_id: UUID | None = None
    session_id: UUID | None = None
    event_type: str = "dograh.session"
    payload: dict = Field(default_factory=dict)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/sessions/route")
async def route_session_event(event: DograhSessionEvent) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(f"{API_BASE_URL}/voice/event", json=event.model_dump(mode="json"))
        response.raise_for_status()
        return {"status": "routed", "orchestrator": response.json()}


@app.post("/audio/process")
async def process_audio(
    call_id: UUID = Form(...),
    session_id: UUID = Form(...),
    language: str = Form("bn-BD"),
    tenant_id: UUID | None = Form(None),
    audio: UploadFile = File(...),
) -> StreamingResponse:
    audio_bytes = await audio.read()
    data = {
        "call_id": str(call_id),
        "session_id": str(session_id),
        "language": language,
    }
    if tenant_id is not None:
        data["tenant_id"] = str(tenant_id)
    async with websockets.connect(f"{API_WS_URL}/voice/ws", open_timeout=5, close_timeout=2) as upstream:
        await upstream.send(
            DograhSocketMessage(
                type="audio",
                payload={
                    **data,
                    "audio_b64": base64.b64encode(audio_bytes).decode("ascii"),
                },
            ).model_dump_json()
        )
        response = DograhSocketMessage.model_validate_json(await upstream.recv())
        if response.type != "audio_result":
            raise RuntimeError(f"Unexpected orchestrator response: {response.type}")
    payload = response.payload
    audio_response = base64.b64decode(payload.get("audio_b64") or "")
    return StreamingResponse(
        iter([audio_response]),
        media_type=payload.get("audio_mime_type", "audio/wav"),
        headers={
            "x-call-id": payload.get("call_id", str(call_id)),
            "x-session-id": payload.get("session_id", str(session_id)),
            "x-transcript": (payload.get("transcript") or "").encode("utf-8").hex(),
            "x-response-text": (payload.get("response_text") or "").encode("utf-8").hex(),
        },
    )


class DograhSocketMessage(BaseModel):
    type: str
    payload: dict = Field(default_factory=dict)
    request_id: str | None = None
    message: str | None = None


class OutboundCallRequest(BaseModel):
    extension: str = "1001"
    caller_id_name: str = "VoxAgent_AI"
    caller_id_number: str = "7000"


@app.post("/outbound/zoiper")
async def outbound_zoiper(payload: OutboundCallRequest) -> dict:
    command = (
        "bgapi originate "
        f"{{origination_caller_id_name={payload.caller_id_name},"
        f"origination_caller_id_number={payload.caller_id_number}}}"
        f"user/{payload.extension} 7000 XML default"
    )
    response = await _send_esl_command(command)
    return {"status": "queued", "extension": payload.extension, "freeswitch": response}


@app.websocket("/ws")
async def websocket_bridge(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        async with websockets.connect(
            f"{API_WS_URL}/voice/ws",
            open_timeout=5,
            close_timeout=2,
        ) as upstream:
            while True:
                message = await websocket.receive_text()
                await upstream.send(message)
                response = await upstream.recv()
                await websocket.send_text(response)
    except WebSocketDisconnect:
        return


@app.websocket("/freeswitch/media")
async def freeswitch_media(websocket: WebSocket) -> None:
    await websocket.accept()
    query = websocket.query_params
    call_id = query.get("call_id")
    from_number = query.get("from") or "unknown"
    to_number = query.get("to") or "7000"
    language = query.get("language") or "bn-BD"
    try:
        async with websockets.connect(
            f"{API_WS_URL}/voice/ws",
            open_timeout=5,
            close_timeout=2,
        ) as upstream:
            await upstream.send(
                DograhSocketMessage(
                    type="start",
                    payload={
                        "call_id": call_id,
                        "from_number": from_number,
                        "to_number": to_number,
                        "direction": "inbound" if to_number == "7000" else "outbound",
                        "language": language,
                        "metadata": {"transport": "freeswitch.mod_audio_stream"},
                    },
                ).model_dump_json()
            )
            started = DograhSocketMessage.model_validate_json(await upstream.recv())
            session_id = started.payload.get("session_id")
            active_call_id = started.payload.get("call_id") or call_id
            pcm_buffer = bytearray()
            chunk_size = DOGRAH_MEDIA_CHUNK_MS * PCM_8K_BYTES_PER_MS

            while True:
                frame = await websocket.receive()
                if frame.get("bytes") is not None:
                    pcm_buffer.extend(frame["bytes"])
                    if len(pcm_buffer) < chunk_size:
                        continue
                    pcm_audio = bytes(pcm_buffer)
                    pcm_buffer.clear()
                    wav_audio = _pcm16_wav(pcm_audio, sample_rate=8000)
                    await upstream.send(
                        DograhSocketMessage(
                            type="audio",
                            payload={
                                "call_id": active_call_id,
                                "session_id": session_id,
                                "language": language,
                                "audio_b64": base64.b64encode(wav_audio).decode("ascii"),
                            },
                        ).model_dump_json()
                    )
                    response = DograhSocketMessage.model_validate_json(await upstream.recv())
                    if response.type == "audio_result":
                        audio_b64 = response.payload.get("audio_b64") or ""
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "streamAudio",
                                    "data": {
                                        "audioDataType": "wav",
                                        "sampleRate": 8000,
                                        "audioData": audio_b64,
                                    },
                                }
                            )
                        )
                elif frame.get("text"):
                    await upstream.send(
                        DograhSocketMessage(
                            type="event",
                            payload={
                                "call_id": active_call_id,
                                "session_id": session_id,
                                "event_type": "freeswitch.media.text",
                                "payload": {"text": frame["text"]},
                            },
                        ).model_dump_json()
                    )
                    await upstream.recv()
    except WebSocketDisconnect:
        if call_id:
            await _end_call(call_id=call_id, session_id=locals().get("session_id"))


def _pcm16_wav(audio: bytes, *, sample_rate: int) -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio)
    return buffer.getvalue()


async def _end_call(*, call_id: str, session_id: str | None) -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"{API_BASE_URL}/voice/end",
            json={"call_id": call_id, "session_id": session_id, "reason": "hangup"},
        )


async def _send_esl_command(command: str) -> str:
    reader, writer = await asyncio.open_connection(
        FREESWITCH_ESL_HOST,
        FREESWITCH_ESL_PORT,
    )
    try:
        await _read_esl_headers(reader)
        writer.write(f"auth {FREESWITCH_EVENT_SOCKET_PASSWORD}\n\n".encode())
        await writer.drain()
        await _read_esl_headers(reader)
        writer.write(f"{command}\n\n".encode())
        await writer.drain()
        headers = await _read_esl_headers(reader)
        return headers.get("Reply-Text") or headers.get("Job-UUID") or "accepted"
    finally:
        writer.close()
        await writer.wait_closed()


async def _read_esl_headers(reader) -> dict[str, str]:
    headers: dict[str, str] = {}
    while True:
        line = (await reader.readline()).decode(errors="ignore").strip()
        if not line:
            return headers
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()
