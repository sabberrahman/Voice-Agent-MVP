from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.voice import VoiceRepository

router = APIRouter()


@router.get("")
async def list_calls(session: AsyncSession = Depends(get_session)) -> dict:
    calls = await VoiceRepository(session).list_calls()
    return {
        "items": [
            {
                "id": call.id,
                "tenant_id": call.tenant_id,
                "direction": call.direction,
                "status": call.status,
                "language": call.metadata_json.get("language") if call.metadata_json else None,
                "started_at": call.started_at,
                "ended_at": call.ended_at,
                "recording_status": "metadata_pending",
                "provider_used": call.metadata_json.get("provider_used") if call.metadata_json else None,
            }
            for call in calls
        ],
        "next_cursor": None,
    }


@router.get("/{call_id}")
async def get_call(call_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    call = await VoiceRepository(session).get_call(call_id)
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")
    return {
        "id": call.id,
        "tenant_id": call.tenant_id,
        "direction": call.direction,
        "status": call.status,
        "from_number": call.from_number,
        "to_number": call.to_number,
        "started_at": call.started_at,
        "ended_at": call.ended_at,
        "metadata": call.metadata_json,
    }
