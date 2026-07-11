from app.providers.stt.base import SpeechToTextProvider, SpeechToTextResult


class GroqSTTProvider(SpeechToTextProvider):
    name = "groq"

    async def transcribe(self, audio: bytes, *, language: str) -> SpeechToTextResult:
        raise NotImplementedError("STT adapter is not implemented yet.")
