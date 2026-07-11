from dataclasses import dataclass

from app.providers.llm.base import LLMMessage


SYSTEM_PROMPT = """You are a polite Bangladeshi customer-service voice agent.
Speak primarily in natural Bangla, but switch naturally into English words when the customer does.
Keep answers short and voice-friendly. Never invent company policy, prices, account facts, or private data.
If you do not know something, say that clearly and offer to create a follow-up ticket.
Support Banglish and mixed Bangla-English input naturally."""


@dataclass
class ConversationContext:
    language: str
    system_prompt: str
    messages: list[LLMMessage]
    available_tools: list[str]
    metadata: dict


class ContextBuilder:
    async def build(
        self,
        *,
        transcript: str,
        history: list[dict],
        language: str,
        tenant_config: dict | None = None,
        call_metadata: dict | None = None,
    ) -> ConversationContext:
        messages = [LLMMessage(role="system", content=SYSTEM_PROMPT)]
        for turn in history[-12:]:
            role = "assistant" if turn.get("speaker") == "assistant" else "user"
            messages.append(LLMMessage(role=role, content=turn.get("text", "")))
        messages.append(LLMMessage(role="user", content=transcript))
        return ConversationContext(
            language=language,
            system_prompt=SYSTEM_PROMPT,
            messages=messages,
            available_tools=[
                "customer_lookup",
                "appointment_booking",
                "ticket_creation",
                "knowledge_search",
                "order_status",
                "crm_lookup",
                "email",
                "webhook",
                "future_mcp_tools",
            ],
            metadata={
                "tenant_config": tenant_config or {},
                "call": call_metadata or {},
                "rag": {"status": "placeholder"},
                "crm": {"status": "placeholder"},
            },
        )
