import httpx

from app.config.settings import Settings
from app.providers.errors import ProviderConfigurationError, ProviderExecutionError
from app.providers.stt.base import SpeechToTextProvider, SpeechToTextResult


class GroqWhisperSTTProvider(SpeechToTextProvider):
    name = "groq"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def transcribe(self, audio: bytes, *, language: str) -> SpeechToTextResult:
        if not self.settings.groq_api_key:
            raise ProviderConfigurationError("GROQ_API_KEY is not configured.")
        files = {"file": ("audio.wav", audio, "audio/wav")}
        data = {
            "model": self.settings.groq_stt_model,
            "language": language.split("-")[0],
            "response_format": "json",
        }
        headers = {"Authorization": f"Bearer {self.settings.groq_api_key}"}
        async with httpx.AsyncClient(timeout=self.settings.stt_timeout_seconds) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                data=data,
                files=files,
            )
        if response.status_code >= 400:
            raise ProviderExecutionError(f"Groq STT failed with status {response.status_code}.")
        payload = response.json()
        return SpeechToTextResult(
            text=payload.get("text", "").strip(),
            language=payload.get("language") or language,
            confidence=None,
            metadata={"provider": self.name, "model": self.settings.groq_stt_model},
        )
