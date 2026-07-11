from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class ConversationState:
    call_id: UUID
    session_id: UUID
    language: str
    current_intent: str | None = None
    last_response: str | None = None
    current_tool_state: dict = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)

    def add_turn(self, speaker: str, text: str, *, language: str, metadata: dict | None = None) -> None:
        self.history.append(
            {
                "speaker": speaker,
                "text": text,
                "language": language,
                "metadata": metadata or {},
            }
        )
        if speaker == "assistant":
            self.last_response = text


class ConversationManager:
    def __init__(self) -> None:
        self._states: dict[str, ConversationState] = {}

    def start(self, call_id: UUID, session_id: UUID, *, language: str) -> ConversationState:
        state = ConversationState(call_id=call_id, session_id=session_id, language=language)
        self._states[str(session_id)] = state
        return state

    def get(self, session_id: UUID) -> ConversationState | None:
        return self._states.get(str(session_id))

    def end(self, session_id: UUID) -> ConversationState | None:
        return self._states.pop(str(session_id), None)

    def active(self) -> list[ConversationState]:
        return list(self._states.values())
