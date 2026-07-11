from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import require_user
from app.config.settings import Settings, get_settings
from app.core.dependencies import get_conversation_manager, get_metrics_collector
from app.db.session import get_redis, get_session
from app.models.domain import Call, CallEvent, Customer, Summary, Tenant, Transcript
from app.observability.metrics import MetricsCollector
from app.providers.factory import ProviderRegistry
from app.voice.conversation import ConversationManager

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_user)])
RECORDINGS_DIR = Path("/recordings")


@router.get("/dashboard")
async def dashboard_overview(
    session: AsyncSession = Depends(get_session),
    conversations: ConversationManager = Depends(get_conversation_manager),
    metrics: MetricsCollector = Depends(get_metrics_collector),
    settings: Settings = Depends(get_settings),
) -> dict:
    now = datetime.now(UTC)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    total_calls = await session.scalar(select(func.count()).select_from(Call)) or 0
    todays_calls = await session.scalar(select(func.count()).select_from(Call).where(Call.created_at >= today)) or 0
    failed_calls = await session.scalar(select(func.count()).select_from(Call).where(Call.status == "failed")) or 0
    completed_calls = await session.scalar(select(func.count()).select_from(Call).where(Call.status == "completed")) or 0
    active_sessions = conversations.active()
    snapshot = metrics.snapshot(active_sessions=len(active_sessions))
    success_rate = round((completed_calls / total_calls) * 100, 2) if total_calls else 100.0
    return {
        "kpis": {
            "active_calls": len(active_sessions),
            "todays_calls": todays_calls,
            "total_calls": total_calls,
            "average_duration_seconds": snapshot.average_call_duration_seconds,
            "average_latency_ms": round(
                (snapshot.average_stt_latency_ms + snapshot.average_llm_latency_ms + snapshot.average_tts_latency_ms)
                / 3,
                2,
            ),
            "success_rate": success_rate,
            "failed_calls": failed_calls,
            "live_sessions": len(active_sessions),
        },
        "provider_usage": snapshot.provider_usage,
        "system_status": {
            "fastapi": "healthy",
            "postgresql": "healthy",
            "redis": "healthy",
            "dograh": "configured",
            "pbx": "configured",
            "nginx": "configured",
            "gpu": "placeholder",
            "storage": "local",
            "health": "healthy",
        },
        "providers": ProviderRegistry(settings).configured(),
        "roadmap": ROADMAP,
    }


@router.get("/live-calls")
async def live_calls(conversations: ConversationManager = Depends(get_conversation_manager)) -> dict:
    return {
        "items": [
            {
                "call_id": state.call_id,
                "session_id": state.session_id,
                "caller": "Zoiper / SIP softphone",
                "duration": "live",
                "language": state.language,
                "current_transcript": _last_turn(state.history, "customer"),
                "ai_response": state.last_response,
                "current_provider": "configured",
                "call_status": "active",
                "audio_streaming_status": "ready",
                "actions": ["end_call", "transfer_placeholder", "mute_placeholder"],
            }
            for state in conversations.active()
        ]
    }


@router.get("/analytics")
async def analytics(session: AsyncSession = Depends(get_session)) -> dict:
    since = datetime.now(UTC) - timedelta(days=14)
    calls = (await session.execute(select(Call).where(Call.created_at >= since))).scalars().all()
    transcripts = (await session.execute(select(Transcript))).scalars().all()
    events = (await session.execute(select(CallEvent))).scalars().all()
    calls_per_day: dict[str, int] = {}
    calls_per_hour: dict[str, int] = {}
    languages: dict[str, int] = {}
    for call in calls:
        calls_per_day[call.created_at.date().isoformat()] = calls_per_day.get(call.created_at.date().isoformat(), 0) + 1
        hour = f"{call.created_at.hour:02d}:00"
        calls_per_hour[hour] = calls_per_hour.get(hour, 0) + 1
    for turn in transcripts:
        languages[turn.language] = languages.get(turn.language, 0) + 1
    provider_usage: dict[str, int] = {}
    for event in events:
        for provider in (event.payload or {}).get("providers", {}).values():
            provider_usage[provider] = provider_usage.get(provider, 0) + 1
    return {
        "calls_per_day": _series(calls_per_day),
        "calls_per_hour": _series(calls_per_hour),
        "languages_used": _series(languages),
        "provider_usage": _series(provider_usage),
        "average_duration": [],
        "average_latency": [],
        "call_success_rate": [],
        "conversation_length": [{"name": "turns", "value": len(transcripts)}],
    }


@router.get("/providers")
async def admin_providers(
    settings: Settings = Depends(get_settings),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> dict:
    registry = ProviderRegistry(settings)
    configured = registry.configured()
    snapshot = metrics.snapshot(active_sessions=0)
    return {
        "configured": configured,
        "available": registry.available(),
        "items": [
            {
                "type": kind.upper(),
                "active_provider": provider,
                "status": "configured",
                "health": "unknown_until_called",
                "latency_ms": getattr(snapshot, f"average_{kind}_latency_ms", 0),
            }
            for kind, provider in configured.items()
        ],
        "future_switching": True,
    }


@router.get("/system")
async def system_status(
    redis=Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> dict:
    redis_status = "healthy"
    if redis is not None:
        try:
            await redis.ping()
        except Exception:  # noqa: BLE001
            redis_status = "unhealthy"
    return {
        "services": [
            {"name": "FastAPI", "status": "healthy", "detail": settings.app_env},
            {"name": "PostgreSQL", "status": "healthy", "detail": settings.postgres_host},
            {"name": "Redis", "status": redis_status, "detail": settings.redis_host},
            {"name": "FreeSWITCH", "status": "configured", "detail": "SIP 1001/1002"},
            {"name": "Dograh", "status": "configured", "detail": settings.api_base_url},
            {"name": "Nginx", "status": "configured", "detail": "reverse proxy"},
            {"name": "Provider APIs", "status": "configured", "detail": "keys masked"},
            {"name": "Storage", "status": "local", "detail": "future S3 backup placeholder"},
            {"name": "CPU", "status": "placeholder", "detail": "host metrics pending"},
            {"name": "RAM", "status": "placeholder", "detail": "host metrics pending"},
            {"name": "GPU", "status": "placeholder", "detail": "no GPU in MVP"},
        ]
    }


@router.get("/settings")
async def admin_settings(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "environment": settings.app_env,
        "providers": {
            "stt": settings.default_stt_provider,
            "llm": settings.default_llm_provider,
            "tts": settings.default_tts_provider,
        },
        "voice": {"default_voice": settings.default_tts_voice, "recording": "enabled"},
        "language": {"primary": settings.default_language, "supported": settings.languages},
        "timeouts": {
            "stt": settings.stt_timeout_seconds,
            "llm": settings.llm_timeout_seconds,
            "tts": settings.tts_timeout_seconds,
        },
        "retry_count": settings.provider_retry_attempts,
        "prompt_settings": {"bangla_first": True, "banglish": True},
        "future_tenant_settings": True,
    }


@router.get("/customers")
async def admin_customers(session: AsyncSession = Depends(get_session)) -> dict:
    customers = (await session.execute(select(Customer).order_by(Customer.created_at.desc()).limit(100))).scalars().all()
    return {
        "items": [
            {
                "id": customer.id,
                "phone": customer.phone_number,
                "name": customer.name,
                "company": customer.metadata_json.get("company") if customer.metadata_json else None,
                "last_call": customer.metadata_json.get("last_call") if customer.metadata_json else None,
                "total_calls": customer.metadata_json.get("total_calls", 0) if customer.metadata_json else 0,
                "preferred_language": customer.language,
                "notes": customer.metadata_json.get("notes") if customer.metadata_json else None,
                "crm_placeholder": True,
            }
            for customer in customers
        ]
    }


@router.post("/seed-zoiper-customers")
async def seed_zoiper_customers(session: AsyncSession = Depends(get_session)) -> dict:
    from app.repositories.voice import DEFAULT_TENANT_ID

    tenant = await session.get(Tenant, DEFAULT_TENANT_ID)
    if tenant is None:
        session.add(
            Tenant(
                id=DEFAULT_TENANT_ID,
                name="Local Development Tenant",
                slug="local-development",
                locale="bn-BD",
                is_active=True,
                settings={},
            )
        )
        await session.flush()

    seeds = [
        {
            "external_id": "zoiper-1001",
            "name": "Zoiper 1001 Test Customer",
            "phone_number": "1001",
            "language": "bn-BD",
            "metadata_json": {
                "company": "Local SIP Lab",
                "notes": "Primary Zoiper user for inbound and outbound AI call testing.",
                "total_calls": 0,
            },
        },
        {
            "external_id": "zoiper-1002",
            "name": "Zoiper 1002 Test Customer",
            "phone_number": "1002",
            "language": "bn-BD",
            "metadata_json": {
                "company": "Local SIP Lab",
                "notes": "Second softphone user for extension-to-extension testing.",
                "total_calls": 0,
            },
        },
    ]
    created = 0
    updated = 0
    for seed in seeds:
        existing = (
            await session.execute(
                select(Customer).where(
                    Customer.tenant_id == DEFAULT_TENANT_ID,
                    Customer.phone_number == seed["phone_number"],
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            session.add(Customer(tenant_id=DEFAULT_TENANT_ID, **seed))
            created += 1
        else:
            existing.external_id = seed["external_id"]
            existing.name = seed["name"]
            existing.language = seed["language"]
            existing.metadata_json = {**(existing.metadata_json or {}), **seed["metadata_json"]}
            updated += 1
    await session.commit()
    return {"status": "seeded", "created": created, "updated": updated, "customers": ["1001", "1002"]}


@router.get("/logs")
async def logs() -> dict:
    return {
        "items": [
            {"level": "info", "message": "Structured JSON logs enabled", "source": "api"},
            {"level": "info", "message": "Loki integration placeholder", "source": "observability"},
            {"level": "info", "message": "Sentry integration placeholder", "source": "observability"},
        ]
    }


@router.get("/knowledge-base")
async def knowledge_base() -> dict:
    return {
        "sources": [],
        "placeholders": ["Future RAG", "Document Upload", "FAQ", "Knowledge Sources"],
    }


@router.get("/campaigns")
async def campaigns() -> dict:
    return {
        "items": [],
        "placeholders": ["Outbound Campaign", "Future Bulk Calling", "Campaign Analytics", "Campaign History"],
    }


@router.post("/simulate-outbound-call")
async def simulate_outbound_call(session: AsyncSession = Depends(get_session)) -> dict:
    from app.repositories.voice import DEFAULT_TENANT_ID, VoiceRepository

    call_id = uuid4()
    repository = VoiceRepository(session)
    tenant_id = await repository.ensure_call(
        call_id=call_id,
        tenant_id=DEFAULT_TENANT_ID,
        direction="outbound",
        language="bn-BD",
    )
    await repository.save_event(
        tenant_id=tenant_id,
        call_id=call_id,
        session_id=None,
        event_type="demo.outbound_call.simulated",
        payload={"status": "queued", "note": "Telephony dialing placeholder for investor demo."},
    )
    return {"call_id": call_id, "status": "queued", "mode": "simulation"}


@router.post("/start-outbound-zoiper/{extension}")
async def start_outbound_zoiper(
    extension: str,
    settings: Settings = Depends(get_settings),
) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.dograh_api_url}/outbound/zoiper",
            json={"extension": extension},
        )
        response.raise_for_status()
        return response.json()


@router.get("/roadmap")
async def roadmap() -> dict:
    return {"items": ROADMAP}


@router.get("/call-details/{call_id}")
async def call_details(call_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    call = await session.get(Call, call_id)
    transcripts = (await session.execute(select(Transcript).where(Transcript.call_id == call_id).order_by(Transcript.created_at))).scalars().all()
    summary = (
        await session.execute(select(Summary).where(Summary.call_id == call_id).order_by(Summary.created_at.desc()).limit(1))
    ).scalar_one_or_none()
    events = (await session.execute(select(CallEvent).where(CallEvent.call_id == call_id).order_by(CallEvent.created_at))).scalars().all()
    return {
        "call": {
            "id": call.id if call else call_id,
            "status": call.status if call else "unknown",
            "customer": call.customer_id if call else None,
            "language_detection": call.metadata_json.get("language") if call and call.metadata_json else "bn-BD",
            "recording": {
                "status": "local" if _recording_path(call_id) else "missing",
                "playback": f"/admin/recordings/{call_id}/playback",
                "download": f"/admin/recordings/{call_id}/download",
                "future_s3_backup": True,
            },
            "estimated_cost": "placeholder",
        },
        "transcript": [
            {
                "speaker": item.speaker,
                "text": item.text,
                "timestamp": item.created_at,
                "language": item.language,
                "confidence": item.confidence,
            }
            for item in transcripts
        ],
        "summary": summary.summary if summary else None,
        "topics": summary.action_items.get("key_topics", []) if summary else [],
        "action_items": summary.action_items.get("action_items", []) if summary else [],
        "sentiment": summary.action_items.get("sentiment", "placeholder") if summary else "placeholder",
        "timeline": [{"time": event.created_at, "type": event.event_type, "payload": event.payload} for event in events],
        "latency": [event.payload for event in events if event.event_type == "voice.audio.processed"],
        "providers_used": [event.payload.get("providers") for event in events if event.payload and "providers" in event.payload],
    }


@router.get("/recordings/{call_id}/playback")
async def recording_playback(call_id: UUID) -> FileResponse:
    path = _recording_path(call_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Recording not found")
    return FileResponse(path, media_type="audio/wav")


@router.get("/recordings/{call_id}/download")
async def recording_download(call_id: UUID) -> FileResponse:
    path = _recording_path(call_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Recording not found")
    return FileResponse(path, media_type="audio/wav", filename=path.name)


def _recording_path(call_id: UUID) -> Path | None:
    matches = sorted(RECORDINGS_DIR.glob(f"{call_id}_*.wav"))
    return matches[-1] if matches else None


ROADMAP = [
    "Phase 1: Zoiper MVP",
    "Phase 2: Real SIP Trunk",
    "Phase 3: Self-hosted STT",
    "Phase 4: Self-hosted TTS",
    "Phase 5: Local LLM",
    "Phase 6: GPU Server",
    "Phase 7: Multiple GPU Servers",
    "Phase 8: Inference Gateway",
    "Phase 9: Multiple PBXs",
    "Phase 10: Enterprise Multi-Tenant SaaS",
]


def _series(values: dict[str, int]) -> list[dict[str, int | str]]:
    return [{"name": key, "value": value} for key, value in sorted(values.items())]


def _last_turn(history: list[dict], speaker: str) -> str | None:
    for turn in reversed(history):
        if turn.get("speaker") == speaker:
            return turn.get("text")
    return None
