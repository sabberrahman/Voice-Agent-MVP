import os
from uuid import UUID

import httpx
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

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
    files = {"audio": (audio.filename or "audio.wav", await audio.read(), audio.content_type or "audio/wav")}
    data = {
        "call_id": str(call_id),
        "session_id": str(session_id),
        "language": language,
    }
    if tenant_id is not None:
        data["tenant_id"] = str(tenant_id)
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(f"{API_BASE_URL}/voice/audio", data=data, files=files)
        response.raise_for_status()
    return StreamingResponse(
        iter([response.content]),
        media_type=response.headers.get("content-type", "audio/wav"),
        headers={
            key: value
            for key, value in response.headers.items()
            if key.lower().startswith("x-")
        },
    )
