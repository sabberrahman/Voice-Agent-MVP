from app.providers.stt.base import SpeechToTextProvider, SpeechToTextResult


class DeepgramSTTProvider(SpeechToTextProvider):
    name = "deepgram"

    async def transcribe(self, audio: bytes, *, language: str) -> SpeechToTextResult:
        raise NotImplementedError("STT adapter is not implemented yet.")
