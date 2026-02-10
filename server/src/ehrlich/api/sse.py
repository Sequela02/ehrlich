import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class SSEEventType(StrEnum):
    PHASE_STARTED = "phase_started"
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    FINDING_RECORDED = "finding_recorded"
    THINKING = "thinking"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass(frozen=True)
class SSEEvent:
    event: SSEEventType
    data: dict[str, Any]

    def format(self) -> str:
        return json.dumps({"event": self.event.value, "data": self.data})
