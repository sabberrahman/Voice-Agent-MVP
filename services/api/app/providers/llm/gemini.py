from app.providers.llm.base import LLMMessage, LLMProvider, LLMResponse


class GeminiLLMProvider(LLMProvider):
    name = "gemini"

    async def generate(self, messages: list[LLMMessage], *, language: str) -> LLMResponse:
        raise NotImplementedError("LLM adapter is not implemented yet.")
