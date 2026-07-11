import httpx

from app.config.settings import Settings
from app.providers.errors import ProviderConfigurationError, ProviderExecutionError
from app.providers.llm.base import LLMMessage, LLMProvider, LLMResponse


class GroqLLMProvider(LLMProvider):
    name = "groq"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings

    async def generate(self, messages: list[LLMMessage], *, language: str) -> LLMResponse:
        if self.settings is None or not self.settings.groq_api_key:
            raise ProviderConfigurationError("GROQ_API_KEY is not configured.")

        payload = {
            "model": self.settings.groq_llm_model,
            "messages": [
                {"role": _normalize_role(message.role), "content": message.content}
                for message in messages
                if message.content
            ],
            "temperature": self.settings.llm_temperature,
            "max_completion_tokens": self.settings.llm_max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
            )
        if response.status_code >= 400:
            raise ProviderExecutionError(f"Groq LLM failed with status {response.status_code}.")

        data = response.json()
        text = _extract_message_text(data)
        return LLMResponse(
            text=text.strip(),
            metadata={"provider": self.name, "model": self.settings.groq_llm_model, "usage": data.get("usage")},
        )


def _normalize_role(role: str) -> str:
    if role in {"system", "assistant", "user"}:
        return role
    return "user"


def _extract_message_text(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    content = choices[0].get("message", {}).get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""
