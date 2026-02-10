from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class DomainEvent:
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class PhaseStarted(DomainEvent):
    phase: str = ""
    investigation_id: str = ""


@dataclass(frozen=True)
class ToolCalled(DomainEvent):
    tool_name: str = ""
    investigation_id: str = ""


@dataclass(frozen=True)
class FindingRecorded(DomainEvent):
    title: str = ""
    investigation_id: str = ""


@dataclass(frozen=True)
class InvestigationCompleted(DomainEvent):
    investigation_id: str = ""
    candidate_count: int = 0
