from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class TextToSpeechResult:
    audio: bytes
    mime_type: str
    metadata: dict | None = None


class TextToSpeechProvider(ABC):
    name: str

    @abstractmethod
    async def synthesize(self, text: str, *, language: str, voice: str | None = None) -> TextToSpeechResult:
        raise NotImplementedError

    async def stream_synthesize(
        self, text: str, *, language: str, voice: str | None = None
    ) -> AsyncIterator[bytes]:
        result = await self.synthesize(text, language=language, voice=voice)
        yield result.audio
