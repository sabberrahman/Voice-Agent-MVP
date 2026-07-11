from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.voice import DEFAULT_TENANT_ID, VoiceRepository

router = APIRouter()
RECORDINGS_DIR = Path("/recordings")


@router.get("")
async def list_calls(session: AsyncSession = Depends(get_session)) -> dict:
    calls = await VoiceRepository(session).list_calls()
    items = [
        {
            "id": call.id,
            "tenant_id": call.tenant_id,
            "direction": call.direction,
            "status": call.status,
            "language": call.metadata_json.get("language") if call.metadata_json else None,
            "started_at": call.started_at,
            "ended_at": call.ended_at,
            "recording_status": "local" if _recording_path(call.id) else "missing",
            "provider_used": call.metadata_json.get("provider_used") if call.metadata_json else None,
        }
        for call in calls
    ]
    known_call_ids = {str(call.id) for call in calls}
    items.extend(_recording_only_items(known_call_ids))
    items.sort(key=lambda item: item.get("started_at") or datetime.min.replace(tzinfo=UTC), reverse=True)
    return {
        "items": items,
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


def _recording_path(call_id: UUID) -> Path | None:
    matches = sorted(RECORDINGS_DIR.glob(f"{call_id}_*.wav"))
    return matches[-1] if matches else None


def _recording_only_items(known_call_ids: set[str]) -> list[dict]:
    items = []
    for path in sorted(RECORDINGS_DIR.glob("*.wav"), key=lambda item: item.stat().st_mtime, reverse=True):
        call_id = path.name.split("_", 1)[0]
        if call_id in known_call_ids:
            continue
        try:
            UUID(call_id)
        except ValueError:
            continue
        items.append(
            {
                "id": call_id,
                "tenant_id": DEFAULT_TENANT_ID,
                "direction": "inbound",
                "status": "recording_only",
                "language": "bn-BD",
                "started_at": datetime.fromtimestamp(path.stat().st_mtime, UTC),
                "ended_at": None,
                "recording_status": "local",
                "provider_used": None,
            }
        )
    return items
