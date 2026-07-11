from app.providers.tts.base import TextToSpeechProvider, TextToSpeechResult


class PiperTTSProvider(TextToSpeechProvider):
    name = "piper"

    async def synthesize(self, text: str, *, language: str, voice: str | None = None) -> TextToSpeechResult:
        raise NotImplementedError("TTS adapter is not implemented yet.")
