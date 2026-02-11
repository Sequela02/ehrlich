from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class HypothesisFormulated(DomainEvent):
    hypothesis_id: str = ""
    statement: str = ""
    rationale: str = ""
    parent_id: str = ""
    investigation_id: str = ""


@dataclass(frozen=True)
class ExperimentStarted(DomainEvent):
    experiment_id: str = ""
    hypothesis_id: str = ""
    description: str = ""
    investigation_id: str = ""


@dataclass(frozen=True)
class ExperimentCompleted(DomainEvent):
    experiment_id: str = ""
    hypothesis_id: str = ""
    tool_count: int = 0
    finding_count: int = 0
    investigation_id: str = ""


@dataclass(frozen=True)
class HypothesisEvaluated(DomainEvent):
    hypothesis_id: str = ""
    status: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    investigation_id: str = ""


@dataclass(frozen=True)
class NegativeControlRecorded(DomainEvent):
    smiles: str = ""
    name: str = ""
    prediction_score: float = 0.0
    correctly_classified: bool = True
    investigation_id: str = ""


@dataclass(frozen=True)
class ToolCalled(DomainEvent):
    tool_name: str = ""
    tool_input: dict[str, Any] = field(default_factory=dict)
    investigation_id: str = ""


@dataclass(frozen=True)
class ToolResultEvent(DomainEvent):
    tool_name: str = ""
    result_preview: str = ""
    investigation_id: str = ""


@dataclass(frozen=True)
class Thinking(DomainEvent):
    text: str = ""
    investigation_id: str = ""


@dataclass(frozen=True)
class FindingRecorded(DomainEvent):
    title: str = ""
    detail: str = ""
    hypothesis_id: str = ""
    evidence_type: str = "neutral"
    evidence: str = ""
    investigation_id: str = ""


@dataclass(frozen=True)
class OutputSummarized(DomainEvent):
    tool_name: str = ""
    original_length: int = 0
    summarized_length: int = 0
    investigation_id: str = ""


@dataclass(frozen=True)
class InvestigationCompleted(DomainEvent):
    investigation_id: str = ""
    candidate_count: int = 0
    summary: str = ""
    cost: dict[str, Any] = field(default_factory=dict)
    candidates: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    negative_controls: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class InvestigationError(DomainEvent):
    error: str = ""
    investigation_id: str = ""
