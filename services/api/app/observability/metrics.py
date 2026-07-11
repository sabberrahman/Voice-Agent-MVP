from dataclasses import dataclass, field


@dataclass
class MetricsSnapshot:
    average_stt_latency_ms: float = 0
    average_llm_latency_ms: float = 0
    average_tts_latency_ms: float = 0
    average_call_duration_seconds: float = 0
    provider_usage: dict[str, int] = field(default_factory=dict)
    failed_calls: int = 0
    active_sessions: int = 0


class MetricsCollector:
    def __init__(self) -> None:
        self.stt_latencies: list[float] = []
        self.llm_latencies: list[float] = []
        self.tts_latencies: list[float] = []
        self.call_durations: list[float] = []
        self.provider_usage: dict[str, int] = {}
        self.failed_calls = 0

    def observe_latency(self, stage: str, milliseconds: float) -> None:
        if stage == "stt":
            self.stt_latencies.append(milliseconds)
        elif stage == "llm":
            self.llm_latencies.append(milliseconds)
        elif stage == "tts":
            self.tts_latencies.append(milliseconds)

    def observe_provider(self, provider: str) -> None:
        self.provider_usage[provider] = self.provider_usage.get(provider, 0) + 1

    def observe_call_duration(self, seconds: float) -> None:
        self.call_durations.append(seconds)

    def mark_failed_call(self) -> None:
        self.failed_calls += 1

    def snapshot(self, *, active_sessions: int) -> MetricsSnapshot:
        return MetricsSnapshot(
            average_stt_latency_ms=_avg(self.stt_latencies),
            average_llm_latency_ms=_avg(self.llm_latencies),
            average_tts_latency_ms=_avg(self.tts_latencies),
            average_call_duration_seconds=_avg(self.call_durations),
            provider_usage=self.provider_usage,
            failed_calls=self.failed_calls,
            active_sessions=active_sessions,
        )


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0
