from functools import lru_cache

from app.config.settings import get_settings
from app.context.builder import ContextBuilder
from app.db.session import get_redis
from app.memory.store import SessionMemoryStore
from app.observability.metrics import MetricsCollector
from app.providers.factory import ProviderRegistry
from app.voice.conversation import ConversationManager
from app.voice.orchestrator import VoiceOrchestrator


@lru_cache
def get_provider_registry() -> ProviderRegistry:
    return ProviderRegistry(get_settings())


@lru_cache
def get_conversation_manager() -> ConversationManager:
    return ConversationManager()


@lru_cache
def get_context_builder() -> ContextBuilder:
    return ContextBuilder()


@lru_cache
def get_metrics_collector() -> MetricsCollector:
    return MetricsCollector()


async def get_voice_orchestrator() -> VoiceOrchestrator:
    return VoiceOrchestrator(
        provider_registry=get_provider_registry(),
        conversation_manager=get_conversation_manager(),
        context_builder=get_context_builder(),
        memory_store=SessionMemoryStore(await get_redis()),
        metrics=get_metrics_collector(),
        settings=get_settings(),
    )
