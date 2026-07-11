from dataclasses import dataclass
from time import perf_counter
from uuid import UUID, uuid4

from app.config.settings import Settings
from app.context.builder import ContextBuilder
from app.memory.store import SessionMemoryStore
from app.observability.metrics import MetricsCollector
from app.providers.errors import ProviderConfigurationError, ProviderExecutionError
from app.providers.factory import ProviderRegistry
from app.providers.llm.base import LLMMessage
from app.providers.retry import retry_async
from app.repositories.voice import VoiceRepository
from app.schemas.voice import (
    VoiceAudioPipelineResult,
    VoiceEndRequest,
    VoiceEventRequest,
    VoiceSessionResponse,
    VoiceStartRequest,
)
from app.voice.conversation import ConversationManager


@dataclass
class VoiceOrchestrator:
    provider_registry: ProviderRegistry
    conversation_manager: ConversationManager
    context_builder: ContextBuilder
    memory_store: SessionMemoryStore
    metrics: MetricsCollector
    settings: Settings

    async def start(
        self, request: VoiceStartRequest, *, repository: VoiceRepository | None = None
    ) -> VoiceSessionResponse:
        call_id = request.call_id or uuid4()
        session_id = uuid4()
        self.conversation_manager.start(call_id, session_id, language=request.language)
        await self.memory_store.save_active_session(
            session_id,
            {"call_id": call_id, "language": request.language, "state": "active"},
        )
        if repository is not None:
            await repository.create_call_session(
                call_id=call_id,
                session_id=session_id,
                tenant_id=request.tenant_id,
                direction=request.direction,
                language=request.language,
                metadata=request.metadata,
            )
            await repository.save_event(
                tenant_id=request.tenant_id,
                call_id=call_id,
                session_id=session_id,
                event_type="voice.start",
                payload=request.model_dump(mode="json"),
            )
        return VoiceSessionResponse(
            call_id=call_id,
            session_id=session_id,
            status="started",
            message="Voice session accepted. AI pipeline is ready.",
            providers=self.provider_registry.configured(),
        )

    async def process_audio(
        self,
        *,
        call_id: UUID,
        session_id: UUID,
        audio: bytes,
        language: str,
        tenant_id: UUID | None = None,
        repository: VoiceRepository | None = None,
    ) -> tuple[VoiceAudioPipelineResult, bytes]:
        state = self.conversation_manager.get(session_id)
        if state is None:
            state = self.conversation_manager.start(call_id, session_id, language=language)

        stt_provider = self.provider_registry.stt()
        llm_provider = self.provider_registry.llm()
        tts_provider = self.provider_registry.tts()
        providers = self.provider_registry.configured()
        latencies: dict[str, float] = {}
        if repository is not None:
            tenant_id = await repository.ensure_call(
                call_id=call_id,
                tenant_id=tenant_id,
                language=language,
            )

        stt_started = perf_counter()
        try:
            transcript_result = await retry_async(
                lambda: stt_provider.transcribe(audio, language=language),
                attempts=self.settings.provider_retry_attempts,
            )
            transcript = transcript_result.text or "আমি স্পষ্টভাবে শুনতে পারিনি। আবার বলবেন?"
            detected_language = transcript_result.language or language
        except (ProviderConfigurationError, ProviderExecutionError, Exception) as exc:  # noqa: BLE001
            transcript = "আমি অডিওটি বুঝতে পারিনি।"
            detected_language = language
            transcript_result = None
            if repository is not None:
                await repository.save_event(
                    tenant_id=tenant_id,
                    call_id=call_id,
                    session_id=session_id,
                    event_type="stt.failed",
                    payload={"error": str(exc), "provider": stt_provider.name},
                )
        latencies["stt"] = round((perf_counter() - stt_started) * 1000, 2)
        self.metrics.observe_latency("stt", latencies["stt"])
        self.metrics.observe_provider(stt_provider.name)

        state.add_turn(
            "customer",
            transcript,
            language=detected_language,
            metadata={"confidence": getattr(transcript_result, "confidence", None)},
        )
        if repository is not None:
            await repository.save_transcript(
                tenant_id=tenant_id,
                call_id=call_id,
                session_id=session_id,
                speaker="customer",
                text=transcript,
                language=detected_language,
                confidence=getattr(transcript_result, "confidence", None),
                metadata={"latency_ms": latencies["stt"], "provider": stt_provider.name},
            )

        context = await self.context_builder.build(
            transcript=transcript,
            history=state.history,
            language=detected_language,
            call_metadata={"call_id": str(call_id), "session_id": str(session_id)},
        )

        llm_started = perf_counter()
        try:
            llm_response = await retry_async(
                lambda: llm_provider.generate(context.messages, language=detected_language),
                attempts=self.settings.provider_retry_attempts,
            )
            response_text = llm_response.text or "দুঃখিত, আমি এখন উত্তর দিতে পারছি না।"
        except (ProviderConfigurationError, ProviderExecutionError, Exception) as exc:  # noqa: BLE001
            response_text = "দুঃখিত, আমি এখন সিস্টেমে সাময়িক সমস্যা পাচ্ছি। একটু পরে আবার চেষ্টা করবেন।"
            if repository is not None:
                await repository.save_event(
                    tenant_id=tenant_id,
                    call_id=call_id,
                    session_id=session_id,
                    event_type="llm.failed",
                    payload={"error": str(exc), "provider": llm_provider.name},
                )
        latencies["llm"] = round((perf_counter() - llm_started) * 1000, 2)
        self.metrics.observe_latency("llm", latencies["llm"])
        self.metrics.observe_provider(llm_provider.name)

        state.add_turn("assistant", response_text, language=detected_language)
        if repository is not None:
            await repository.save_transcript(
                tenant_id=tenant_id,
                call_id=call_id,
                session_id=session_id,
                speaker="assistant",
                text=response_text,
                language=detected_language,
                confidence=None,
                metadata={"latency_ms": latencies["llm"], "provider": llm_provider.name},
            )

        tts_started = perf_counter()
        try:
            tts_result = await retry_async(
                lambda: tts_provider.synthesize(
                    response_text,
                    language=detected_language,
                    voice=self.settings.default_tts_voice,
                ),
                attempts=self.settings.provider_retry_attempts,
            )
            audio_response = tts_result.audio
            audio_mime_type = tts_result.mime_type
        except (ProviderConfigurationError, ProviderExecutionError, Exception) as exc:  # noqa: BLE001
            audio_response = response_text.encode("utf-8")
            audio_mime_type = "text/plain; charset=utf-8"
            if repository is not None:
                await repository.save_event(
                    tenant_id=tenant_id,
                    call_id=call_id,
                    session_id=session_id,
                    event_type="tts.failed",
                    payload={"error": str(exc), "provider": tts_provider.name},
                )
        latencies["tts"] = round((perf_counter() - tts_started) * 1000, 2)
        self.metrics.observe_latency("tts", latencies["tts"])
        self.metrics.observe_provider(tts_provider.name)

        await self.memory_store.save_active_session(
            session_id,
            {
                "call_id": call_id,
                "language": detected_language,
                "last_response": response_text,
                "history": state.history[-12:],
            },
        )
        if repository is not None:
            await repository.save_event(
                tenant_id=tenant_id,
                call_id=call_id,
                session_id=session_id,
                event_type="voice.audio.processed",
                payload={"latencies_ms": latencies, "providers": providers},
            )

        return (
            VoiceAudioPipelineResult(
                call_id=call_id,
                session_id=session_id,
                transcript=transcript,
                response_text=response_text,
                language=detected_language,
                providers=providers,
                latencies_ms=latencies,
                audio_mime_type=audio_mime_type,
            ),
            audio_response,
        )

    async def end(
        self,
        request: VoiceEndRequest,
        *,
        repository: VoiceRepository | None = None,
        tenant_id: UUID | None = None,
    ) -> VoiceSessionResponse:
        state = self.conversation_manager.end(request.session_id) if request.session_id else None
        if request.session_id:
            await self.memory_store.delete_active_session(request.session_id)
        if state is not None and repository is not None:
            summary_text = await self._generate_summary(state.history, state.language)
            await repository.save_summary(
                tenant_id=tenant_id,
                call_id=request.call_id,
                language=state.language,
                summary=summary_text,
                action_items={
                    "key_topics": [],
                    "action_items": [],
                    "sentiment": "placeholder",
                    "language_used": state.language,
                    "cost_estimation": "placeholder",
                },
            )
            await repository.save_event(
                tenant_id=tenant_id,
                call_id=request.call_id,
                session_id=request.session_id,
                event_type="voice.end",
                payload=request.model_dump(mode="json"),
            )
        return VoiceSessionResponse(
            call_id=request.call_id,
            session_id=request.session_id,
            status="ended",
            message=request.reason or "Voice session ended.",
            providers=self.provider_registry.configured(),
        )

    async def event(self, request: VoiceEventRequest) -> VoiceSessionResponse:
        return VoiceSessionResponse(
            call_id=request.call_id,
            session_id=request.session_id,
            status="event_received",
            message=f"Accepted event: {request.event_type}",
            providers=self.provider_registry.configured(),
        )

    async def _generate_summary(self, history: list[dict], language: str) -> str:
        if not history:
            return "No conversation turns were captured."
        summary_prompt = [
            {
                "speaker": turn.get("speaker"),
                "text": turn.get("text"),
                "language": turn.get("language"),
            }
            for turn in history[-30:]
        ]
        provider = self.provider_registry.llm()
        try:
            response = await retry_async(
                lambda: provider.generate(
                    [
                        LLMMessage(
                            role="system",
                            content=(
                                "Summarize this customer-service voice call in concise Bangla. "
                                "Include key topics, requested actions, and unresolved items. "
                                "Do not invent facts."
                            ),
                        ),
                        LLMMessage(role="user", content=str(summary_prompt)),
                    ],
                    language=language,
                ),
                attempts=1,
            )
            return response.text
        except Exception:  # noqa: BLE001
            return f"Conversation ended with {len(history)} captured turns. Details are stored in transcript."
