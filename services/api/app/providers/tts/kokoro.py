from app.providers.tts.base import TextToSpeechProvider, TextToSpeechResult


class KokoroTTSProvider(TextToSpeechProvider):
    name = "kokoro"

    async def synthesize(self, text: str, *, language: str, voice: str | None = None) -> TextToSpeechResult:
        raise NotImplementedError("TTS adapter is not implemented yet.")
