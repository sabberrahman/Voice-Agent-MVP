from app.providers.stt.base import SpeechToTextProvider, SpeechToTextResult


class FasterWhisperSTTProvider(SpeechToTextProvider):
    name = "faster_whisper"

    async def transcribe(self, audio: bytes, *, language: str) -> SpeechToTextResult:
        raise NotImplementedError("STT adapter is not implemented yet.")
