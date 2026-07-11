from fastapi import APIRouter, Depends

from app.core.dependencies import get_conversation_manager, get_metrics_collector
from app.observability.metrics import MetricsCollector
from app.voice.conversation import ConversationManager

router = APIRouter()


@router.get("/metrics")
async def metrics(
    collector: MetricsCollector = Depends(get_metrics_collector),
    conversations: ConversationManager = Depends(get_conversation_manager),
) -> dict:
    return collector.snapshot(active_sessions=len(conversations.active())).__dict__
