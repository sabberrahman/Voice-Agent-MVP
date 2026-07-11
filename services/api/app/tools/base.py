from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolRequest:
    name: str
    arguments: dict
    tenant_id: str | None = None
    call_id: str | None = None


@dataclass(frozen=True)
class ToolResult:
    name: str
    content: dict
    success: bool = True


class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    async def execute(self, request: ToolRequest) -> ToolResult:
        raise NotImplementedError
