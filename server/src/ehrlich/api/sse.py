import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ehrlich.investigation.domain.events import (
    DomainEvent,
    FindingRecorded,
    InvestigationCompleted,
    InvestigationError,
    PhaseStarted,
    Thinking,
    ToolCalled,
    ToolResultEvent,
)


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


def domain_event_to_sse(event: DomainEvent) -> SSEEvent | None:
    if isinstance(event, PhaseStarted):
        return SSEEvent(
            event=SSEEventType.PHASE_STARTED,
            data={"phase": event.phase, "investigation_id": event.investigation_id},
        )
    if isinstance(event, ToolCalled):
        return SSEEvent(
            event=SSEEventType.TOOL_CALLED,
            data={
                "tool_name": event.tool_name,
                "tool_input": event.tool_input,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, ToolResultEvent):
        return SSEEvent(
            event=SSEEventType.TOOL_RESULT,
            data={
                "tool_name": event.tool_name,
                "result_preview": event.result_preview,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, FindingRecorded):
        return SSEEvent(
            event=SSEEventType.FINDING_RECORDED,
            data={
                "title": event.title,
                "detail": event.detail,
                "phase": event.phase,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, Thinking):
        return SSEEvent(
            event=SSEEventType.THINKING,
            data={"text": event.text, "investigation_id": event.investigation_id},
        )
    if isinstance(event, InvestigationError):
        return SSEEvent(
            event=SSEEventType.ERROR,
            data={"error": event.error, "investigation_id": event.investigation_id},
        )
    if isinstance(event, InvestigationCompleted):
        return SSEEvent(
            event=SSEEventType.COMPLETED,
            data={
                "investigation_id": event.investigation_id,
                "candidate_count": event.candidate_count,
                "summary": event.summary,
                "cost": event.cost,
            },
        )
    return None
