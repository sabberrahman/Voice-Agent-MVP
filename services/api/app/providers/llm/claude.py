import httpx

from app.config.settings import Settings
from app.providers.errors import ProviderConfigurationError, ProviderExecutionError
from app.providers.llm.base import LLMMessage, LLMProvider, LLMResponse


class ClaudeLLMProvider(LLMProvider):
    name = "claude"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings

    async def generate(self, messages: list[LLMMessage], *, language: str) -> LLMResponse:
        if self.settings is None or not self.settings.anthropic_api_key:
            raise ProviderConfigurationError("ANTHROPIC_API_KEY is not configured.")
        system = "\n\n".join(message.content for message in messages if message.role == "system")
        user_messages = [
            {"role": message.role, "content": message.content}
            for message in messages
            if message.role in {"user", "assistant"}
        ]
        payload = {
            "model": self.settings.anthropic_model,
            "max_tokens": self.settings.llm_max_tokens,
            "system": system,
            "messages": user_messages,
        }
        headers = {
            "x-api-key": self.settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
            response = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
        if response.status_code >= 400:
            raise ProviderExecutionError(f"Claude LLM failed with status {response.status_code}.")
        data = response.json()
        text = "".join(part.get("text", "") for part in data.get("content", []) if part.get("type") == "text")
        return LLMResponse(
            text=text.strip(),
            metadata={"provider": self.name, "model": self.settings.anthropic_model, "usage": data.get("usage")},
        )
