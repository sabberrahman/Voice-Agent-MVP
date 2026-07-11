from app.providers.llm.base import LLMMessage, LLMProvider, LLMResponse


class LocalVLLMProvider(LLMProvider):
    name = "local_vllm"

    async def generate(self, messages: list[LLMMessage], *, language: str) -> LLMResponse:
        raise NotImplementedError("LLM adapter is not implemented yet.")
