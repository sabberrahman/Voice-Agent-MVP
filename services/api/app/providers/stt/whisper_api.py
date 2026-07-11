from app.providers.stt.base import SpeechToTextProvider, SpeechToTextResult


class WhisperAPISTTProvider(SpeechToTextProvider):
    name = "whisper_api"

    async def transcribe(self, audio: bytes, *, language: str) -> SpeechToTextResult:
        raise NotImplementedError("STT adapter is not implemented yet.")
