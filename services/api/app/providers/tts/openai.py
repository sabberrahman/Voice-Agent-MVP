import httpx

from app.config.settings import Settings
from app.providers.errors import ProviderConfigurationError, ProviderExecutionError
from app.providers.tts.base import TextToSpeechProvider, TextToSpeechResult


class OpenAITTSProvider(TextToSpeechProvider):
    name = "openai"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings

    async def synthesize(self, text: str, *, language: str, voice: str | None = None) -> TextToSpeechResult:
        if self.settings is None or not self.settings.openai_api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY is not configured.")
        payload = {
            "model": self.settings.openai_tts_model,
            "voice": voice or self.settings.default_tts_voice or "alloy",
            "input": text,
            "response_format": "wav",
        }
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.settings.tts_timeout_seconds) as client:
            response = await client.post("https://api.openai.com/v1/audio/speech", json=payload, headers=headers)
        if response.status_code >= 400:
            raise ProviderExecutionError(f"OpenAI TTS failed with status {response.status_code}.")
        return TextToSpeechResult(
            audio=response.content,
            mime_type="audio/wav",
            metadata={"provider": self.name, "model": self.settings.openai_tts_model},
        )
