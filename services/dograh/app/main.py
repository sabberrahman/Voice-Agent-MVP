import asyncio
import audioop
import base64
import json
import logging
import os
import wave
from io import BytesIO
from pathlib import Path
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
DOGRAH_MIN_AUDIO_RMS = int(os.getenv("DOGRAH_MIN_AUDIO_RMS", "50"))
DOGRAH_GREETING_TEXT = os.getenv("DOGRAH_GREETING_TEXT", "Hello, VoxAgent is ready. How can I help you?")
DOGRAH_DEFAULT_LANGUAGE = os.getenv("DOGRAH_DEFAULT_LANGUAGE") or os.getenv("DEFAULT_LANGUAGE", "bn-BD")
DOGRAH_ENABLE_TTS = os.getenv("DOGRAH_ENABLE_TTS", os.getenv("ENABLE_TTS", "true")).lower() in {
    "1",
    "true",
    "yes",
    "on",
}
RECORDINGS_DIR = Path(os.getenv("DOGRAH_RECORDINGS_DIR", "/recordings"))
PCM_8K_BYTES_PER_MS = 16
logger = logging.getLogger("voxagent.dograh")

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
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/voice/audio",
            data=data,
            files={"audio": (audio.filename or "audio.wav", audio_bytes, audio.content_type or "audio/wav")},
        )
        response.raise_for_status()
    audio_response = response.content
    return StreamingResponse(
        iter([audio_response]),
        media_type=response.headers.get("content-type", "audio/wav"),
        headers={
            "x-call-id": response.headers.get("x-call-id", str(call_id)),
            "x-session-id": response.headers.get("x-session-id", str(session_id)),
            "x-transcript": response.headers.get("x-transcript", ""),
            "x-response-text": response.headers.get("x-response-text", ""),
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


class SpeakRequest(BaseModel):
    call_id: UUID
    session_id: UUID
    tenant_id: UUID | None = None
    language: str = "bn-BD"
    text: str = DOGRAH_GREETING_TEXT


@app.post("/speak")
async def speak_text(payload: SpeakRequest) -> StreamingResponse:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/voice/speak",
            json=payload.model_dump(mode="json"),
        )
        response.raise_for_status()
    return StreamingResponse(
        iter([response.content]),
        media_type=response.headers.get("content-type", "audio/wav"),
        headers={
            "x-call-id": response.headers.get("x-call-id", str(payload.call_id)),
            "x-session-id": response.headers.get("x-session-id", str(payload.session_id)),
            "x-response-text": response.headers.get("x-response-text", ""),
        },
    )


@app.post("/outbound/zoiper")
async def outbound_zoiper(payload: OutboundCallRequest) -> dict:
    command = (
        "bgapi originate "
        f"{{origination_caller_id_name={payload.caller_id_name},"
        f"origination_caller_id_number={payload.caller_id_number}}}"
        f"user/{payload.extension} 7000 XML default"
    )
    try:
        response = await _send_esl_command(command)
    except OSError as exc:
        response = f"accepted_with_socket_close: {exc}"
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
    language = query.get("language") or DOGRAH_DEFAULT_LANGUAGE
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
            skipped_silence_chunks = 0
            if DOGRAH_ENABLE_TTS:
                await upstream.send(
                    DograhSocketMessage(
                        type="speak",
                        payload={
                            "call_id": active_call_id,
                            "session_id": session_id,
                            "language": language,
                            "text": DOGRAH_GREETING_TEXT,
                        },
                    ).model_dump_json()
                )
                greeting = DograhSocketMessage.model_validate_json(await upstream.recv())
                if greeting.type == "audio_result":
                    if not await _send_freeswitch_audio(
                        websocket,
                        greeting.payload,
                        call_id=active_call_id,
                    ):
                        return

            while True:
                frame = await websocket.receive()
                if frame.get("bytes") is not None:
                    pcm_buffer.extend(frame["bytes"])
                    if len(pcm_buffer) < chunk_size:
                        continue
                    pcm_audio = bytes(pcm_buffer)
                    pcm_buffer.clear()
                    rms = audioop.rms(pcm_audio, 2) if pcm_audio else 0
                    peak = audioop.max(pcm_audio, 2) if pcm_audio else 0
                    if rms < DOGRAH_MIN_AUDIO_RMS:
                        skipped_silence_chunks += 1
                        if skipped_silence_chunks == 1 or skipped_silence_chunks % 10 == 0:
                            logger.info(
                                "Skipping low-energy caller audio for call %s: rms=%s peak=%s bytes=%s skipped=%s",
                                active_call_id,
                                rms,
                                peak,
                                len(pcm_audio),
                                skipped_silence_chunks,
                            )
                        continue
                    skipped_silence_chunks = 0
                    logger.info(
                        "Forwarding caller audio to STT for call %s: rms=%s peak=%s bytes=%s",
                        active_call_id,
                        rms,
                        peak,
                        len(pcm_audio),
                    )
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
                        if not await _send_freeswitch_audio(
                            websocket,
                            response.payload,
                            call_id=active_call_id,
                        ):
                            return
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
    except RuntimeError:
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


async def _send_freeswitch_audio(websocket: WebSocket, payload: dict, *, call_id: str) -> bool:
    audio = base64.b64decode(payload.get("audio_b64") or "")
    if not audio:
        return True
    if await _broadcast_audio_file(call_id=call_id, audio=audio):
        return True
    audio_data_type = "raw"
    try:
        audio = _wav_to_pcm16(audio)
    except wave.Error:
        audio_data_type = "wav"
    try:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "streamAudio",
                    "data": {
                        "audioDataType": audio_data_type,
                        "sampleRate": 8000,
                        "audioData": base64.b64encode(audio).decode("ascii"),
                    },
                }
            )
        )
        return True
    except RuntimeError:
        return False


def _wav_to_pcm16(audio: bytes) -> bytes:
    with wave.open(BytesIO(audio), "rb") as wav:
        return wav.readframes(wav.getnframes())


async def _broadcast_audio_file(*, call_id: str, audio: bytes) -> bool:
    if not call_id:
        return False
    call_recordings_dir = RECORDINGS_DIR / "tts"
    call_recordings_dir.mkdir(parents=True, exist_ok=True)
    audio_path = call_recordings_dir / f"{call_id}_{int(asyncio.get_running_loop().time() * 1000)}.wav"
    try:
        try:
            with wave.open(BytesIO(audio), "rb"):
                audio_path.write_bytes(audio)
        except wave.Error:
            audio_path.write_bytes(_pcm16_wav(audio, sample_rate=8000))
        response = await _send_esl_command(f"uuid_broadcast {call_id} {audio_path} aleg")
        return "+OK" in response or "accepted" in response.lower()
    except Exception:  # noqa: BLE001
        return False


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
        try:
            writer.close()
            await writer.wait_closed()
        except OSError:
            pass


async def _read_esl_headers(reader) -> dict[str, str]:
    headers: dict[str, str] = {}
    while True:
        line = (await reader.readline()).decode(errors="ignore").strip()
        if not line:
            return headers
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()
