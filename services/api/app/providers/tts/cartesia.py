import httpx

from app.config.settings import Settings
from app.providers.errors import ProviderConfigurationError, ProviderExecutionError
from app.providers.tts.base import TextToSpeechProvider, TextToSpeechResult


class CartesiaTTSProvider(TextToSpeechProvider):
    name = "cartesia"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings

    async def synthesize(self, text: str, *, language: str, voice: str | None = None) -> TextToSpeechResult:
        if self.settings is None or not self.settings.cartesia_api_key:
            raise ProviderConfigurationError("CARTESIA_API_KEY is not configured.")
        voice_id = voice or self.settings.cartesia_voice_id
        if not voice_id:
            raise ProviderConfigurationError("CARTESIA_VOICE_ID or DEFAULT_TTS_VOICE is not configured.")
        payload = {
            "model_id": self.settings.cartesia_model,
            "transcript": text,
            "voice": {"mode": "id", "id": voice_id},
            "language": language.split("-")[0],
            "output_format": {"container": "wav", "encoding": "pcm_s16le", "sample_rate": 8000},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.cartesia_api_key}",
            "Cartesia-Version": self.settings.cartesia_version,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.settings.tts_timeout_seconds) as client:
            response = await client.post("https://api.cartesia.ai/tts/bytes", json=payload, headers=headers)
        if response.status_code >= 400:
            raise ProviderExecutionError(f"Cartesia TTS failed with status {response.status_code}.")
        return TextToSpeechResult(
            audio=response.content,
            mime_type="audio/wav",
            metadata={"provider": self.name, "model": self.settings.cartesia_model},
        )
