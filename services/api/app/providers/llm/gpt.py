import httpx

from app.config.settings import Settings
from app.providers.errors import ProviderConfigurationError, ProviderExecutionError
from app.providers.llm.base import LLMMessage, LLMProvider, LLMResponse


class GPTLLMProvider(LLMProvider):
    name = "gpt"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings

    async def generate(self, messages: list[LLMMessage], *, language: str) -> LLMResponse:
        if self.settings is None or not self.settings.openai_api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY is not configured.")
        input_text = "\n".join(f"{message.role}: {message.content}" for message in messages)
        payload = {
            "model": self.settings.openai_model,
            "input": input_text,
            "max_output_tokens": self.settings.llm_max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
            response = await client.post("https://api.openai.com/v1/responses", json=payload, headers=headers)
        if response.status_code >= 400:
            raise ProviderExecutionError(f"OpenAI LLM failed with status {response.status_code}.")
        data = response.json()
        text = data.get("output_text") or _extract_output_text(data)
        return LLMResponse(
            text=text.strip(),
            metadata={"provider": self.name, "model": self.settings.openai_model, "usage": data.get("usage")},
        )


def _extract_output_text(payload: dict) -> str:
    parts: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                parts.append(content.get("text", ""))
    return "".join(parts)
