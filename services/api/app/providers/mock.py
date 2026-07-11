from app.providers.llm.base import LLMMessage, LLMProvider, LLMResponse
from app.providers.stt.base import SpeechToTextProvider, SpeechToTextResult
from app.providers.tts.base import TextToSpeechProvider, TextToSpeechResult


class MockSTTProvider(SpeechToTextProvider):
    name = "mock_stt"

    async def transcribe(self, audio: bytes, *, language: str) -> SpeechToTextResult:
        return SpeechToTextResult(
            text="আমি আপনার কথা পেয়েছি।",
            language=language,
            confidence=0.0,
            metadata={"provider": self.name, "bytes": len(audio)},
        )


class MockLLMProvider(LLMProvider):
    name = "mock_llm"

    async def generate(self, messages: list[LLMMessage], *, language: str) -> LLMResponse:
        return LLMResponse(
            text="ধন্যবাদ। আমি বিষয়টা বুঝেছি। একটু বিস্তারিত বলবেন?",
            metadata={"provider": self.name},
        )


class MockTTSProvider(TextToSpeechProvider):
    name = "mock_tts"

    async def synthesize(self, text: str, *, language: str, voice: str | None = None) -> TextToSpeechResult:
        return TextToSpeechResult(
            audio=text.encode("utf-8"),
            mime_type="text/plain; charset=utf-8",
            metadata={"provider": self.name, "voice": voice},
        )
