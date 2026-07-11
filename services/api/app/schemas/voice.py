from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VoiceStartRequest(BaseModel):
    tenant_id: UUID | None = None
    call_id: UUID | None = None
    from_number: str | None = None
    to_number: str | None = None
    direction: str = "inbound"
    language: str = "bn-BD"
    metadata: dict = Field(default_factory=dict)


class VoiceEndRequest(BaseModel):
    call_id: UUID
    session_id: UUID | None = None
    reason: str | None = None
    metadata: dict = Field(default_factory=dict)


class VoiceEventRequest(BaseModel):
    call_id: UUID | None = None
    session_id: UUID | None = None
    event_type: str
    payload: dict = Field(default_factory=dict)


class VoiceSpeakRequest(BaseModel):
    call_id: UUID
    session_id: UUID
    tenant_id: UUID | None = None
    language: str = "bn-BD"
    text: str


class ProviderSelectionRequest(BaseModel):
    stt_provider: str | None = None
    llm_provider: str | None = None
    tts_provider: str | None = None


class VoiceSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    call_id: UUID | None = None
    session_id: UUID | None = None
    status: str
    message: str
    providers: dict[str, str] = Field(default_factory=dict)


class VoiceAudioPipelineResult(BaseModel):
    call_id: UUID
    session_id: UUID
    transcript: str
    response_text: str
    language: str
    providers: dict[str, str]
    latencies_ms: dict[str, float]
    audio_mime_type: str
