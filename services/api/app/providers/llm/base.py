from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMResponse:
    text: str
    metadata: dict | None = None


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, messages: list[LLMMessage], *, language: str) -> LLMResponse:
        raise NotImplementedError

    async def stream_generate(
        self, messages: list[LLMMessage], *, language: str
    ) -> AsyncIterator[str]:
        response = await self.generate(messages, language=language)
        yield response.text
