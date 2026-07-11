from app.providers.llm.base import LLMMessage, LLMProvider, LLMResponse


class DeepSeekLLMProvider(LLMProvider):
    name = "deepseek"

    async def generate(self, messages: list[LLMMessage], *, language: str) -> LLMResponse:
        raise NotImplementedError("LLM adapter is not implemented yet.")
