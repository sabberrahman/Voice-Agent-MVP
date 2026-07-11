from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.voice import VoiceRepository

router = APIRouter()


@router.get("/transcripts/{call_id}")
async def get_transcript(call_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    turns = await VoiceRepository(session).get_transcript(call_id)
    if not turns:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return {
        "call_id": call_id,
        "items": [
            {
                "id": turn.id,
                "timestamp": turn.created_at,
                "speaker": turn.speaker,
                "original_transcript": turn.text,
                "detected_language": turn.language,
                "confidence": turn.confidence,
            }
            for turn in turns
        ],
    }


@router.get("/summary/{call_id}")
async def get_summary(call_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    summary = await VoiceRepository(session).get_summary(call_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not found")
    return {
        "call_id": call_id,
        "summary": summary.summary,
        "language": summary.language,
        "key_topics": summary.action_items.get("key_topics", []),
        "action_items": summary.action_items.get("action_items", []),
        "sentiment": summary.action_items.get("sentiment", "placeholder"),
        "duration": summary.action_items.get("duration", "placeholder"),
        "language_used": summary.action_items.get("language_used"),
    }
