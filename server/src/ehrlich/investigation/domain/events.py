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
    prediction: str = ""
    null_prediction: str = ""
    success_criteria: str = ""
    failure_criteria: str = ""
    scope: str = ""
    hypothesis_type: str = ""
    prior_confidence: float = 0.0
    parent_id: str = ""
    investigation_id: str = ""


@dataclass(frozen=True)
class ExperimentStarted(DomainEvent):
    experiment_id: str = ""
    hypothesis_id: str = ""
    description: str = ""
    independent_variable: str = ""
    dependent_variable: str = ""
    controls: list[str] = field(default_factory=list)
    analysis_plan: str = ""
    success_criteria: str = ""
    failure_criteria: str = ""
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
    certainty_of_evidence: str = ""
    investigation_id: str = ""


@dataclass(frozen=True)
class NegativeControlRecorded(DomainEvent):
    identifier: str = ""
    identifier_type: str = ""
    name: str = ""
    score: float = 0.0
    threshold: float = 0.5
    correctly_classified: bool = True
    investigation_id: str = ""


@dataclass(frozen=True)
class PositiveControlRecorded(DomainEvent):
    identifier: str = ""
    identifier_type: str = ""
    name: str = ""
    known_activity: str = ""
    score: float = 0.0
    correctly_classified: bool = True
    investigation_id: str = ""


@dataclass(frozen=True)
class ValidationMetricsComputed(DomainEvent):
    z_prime: float | None = None
    z_prime_quality: str = ""
    positive_control_count: int = 0
    negative_control_count: int = 0
    positive_mean: float = 0.0
    negative_mean: float = 0.0
    investigation_id: str = ""


@dataclass(frozen=True)
class ToolCalled(DomainEvent):
    tool_name: str = ""
    tool_input: dict[str, Any] = field(default_factory=dict)
    experiment_id: str = ""
    investigation_id: str = ""


@dataclass(frozen=True)
class ToolResultEvent(DomainEvent):
    tool_name: str = ""
    result_preview: str = ""
    experiment_id: str = ""
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
    source_type: str = ""
    source_id: str = ""
    evidence_level: int = 0
    investigation_id: str = ""


@dataclass(frozen=True)
class OutputSummarized(DomainEvent):
    tool_name: str = ""
    original_length: int = 0
    summarized_length: int = 0
    investigation_id: str = ""


@dataclass(frozen=True)
class HypothesisApprovalRequested(DomainEvent):
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    investigation_id: str = ""


@dataclass(frozen=True)
class PhaseChanged(DomainEvent):
    phase: int = 0
    name: str = ""
    description: str = ""
    investigation_id: str = ""


@dataclass(frozen=True)
class CostUpdate(DomainEvent):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    tool_calls: int = 0
    investigation_id: str = ""


@dataclass(frozen=True)
class DomainDetected(DomainEvent):
    domain: str = ""
    display_config: dict[str, Any] = field(default_factory=dict)
    investigation_id: str = ""


@dataclass(frozen=True)
class LiteratureSurveyCompleted(DomainEvent):
    pico: dict[str, str] = field(default_factory=dict)
    search_queries: int = 0
    total_results: int = 0
    included_results: int = 0
    evidence_grade: str = ""
    assessment: str = ""
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
    positive_controls: list[dict[str, Any]] = field(default_factory=list)
    validation_metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InvestigationError(DomainEvent):
    error: str = ""
    investigation_id: str = ""
