from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_conversation_manager, get_metrics_collector
from app.db.session import get_session
from app.observability.metrics import MetricsCollector
from app.repositories.voice import VoiceRepository
from app.voice.conversation import ConversationManager

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    session: AsyncSession = Depends(get_session),
    conversations: ConversationManager = Depends(get_conversation_manager),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> str:
    calls = await VoiceRepository(session).list_calls(limit=25)
    snapshot = metrics.snapshot(active_sessions=len(conversations.active()))
    rows = "".join(
        f"<tr><td>{call.id}</td><td>{call.status}</td><td>{call.direction}</td>"
        f"<td>{call.started_at or ''}</td><td>{call.ended_at or ''}</td></tr>"
        for call in calls
    )
    return f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>VoxAgent Internal Dashboard</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 32px; color: #18202a; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
        th, td {{ border-bottom: 1px solid #d8dee6; padding: 8px; text-align: left; }}
        .metric {{ display: inline-block; margin-right: 24px; padding: 8px 0; }}
      </style>
    </head>
    <body>
      <h1>VoxAgent Internal Dashboard</h1>
      <div class="metric">Active Calls: {snapshot.active_sessions}</div>
      <div class="metric">Avg STT: {snapshot.average_stt_latency_ms} ms</div>
      <div class="metric">Avg LLM: {snapshot.average_llm_latency_ms} ms</div>
      <div class="metric">Avg TTS: {snapshot.average_tts_latency_ms} ms</div>
      <div class="metric">Failed Calls: {snapshot.failed_calls}</div>
      <h2>Call History</h2>
      <table>
        <thead><tr><th>ID</th><th>Status</th><th>Direction</th><th>Started</th><th>Ended</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </body>
    </html>
    """
