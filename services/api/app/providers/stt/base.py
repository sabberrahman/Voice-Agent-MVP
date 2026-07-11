from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections.abc import AsyncIterator


@dataclass(frozen=True)
class SpeechToTextResult:
    text: str
    language: str
    confidence: float | None = None
    metadata: dict | None = None


class SpeechToTextProvider(ABC):
    name: str

    @abstractmethod
    async def transcribe(self, audio: bytes, *, language: str) -> SpeechToTextResult:
        raise NotImplementedError

    async def stream_transcribe(
        self, audio_chunks: AsyncIterator[bytes], *, language: str
    ) -> AsyncIterator[SpeechToTextResult]:
        buffer = bytearray()
        async for chunk in audio_chunks:
            buffer.extend(chunk)
        yield await self.transcribe(bytes(buffer), language=language)
