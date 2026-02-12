import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ehrlich.investigation.domain.events import (
    CostUpdate,
    DomainDetected,
    DomainEvent,
    ExperimentCompleted,
    ExperimentStarted,
    FindingRecorded,
    HypothesisApprovalRequested,
    HypothesisEvaluated,
    HypothesisFormulated,
    InvestigationCompleted,
    InvestigationError,
    LiteratureSurveyCompleted,
    NegativeControlRecorded,
    OutputSummarized,
    PhaseChanged,
    PositiveControlRecorded,
    Thinking,
    ToolCalled,
    ToolResultEvent,
    ValidationMetricsComputed,
    VisualizationRendered,
)


class SSEEventType(StrEnum):
    HYPOTHESIS_FORMULATED = "hypothesis_formulated"
    EXPERIMENT_STARTED = "experiment_started"
    EXPERIMENT_COMPLETED = "experiment_completed"
    HYPOTHESIS_EVALUATED = "hypothesis_evaluated"
    NEGATIVE_CONTROL = "negative_control"
    POSITIVE_CONTROL = "positive_control"
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    FINDING_RECORDED = "finding_recorded"
    THINKING = "thinking"
    ERROR = "error"
    COMPLETED = "completed"
    OUTPUT_SUMMARIZED = "output_summarized"
    PHASE_CHANGED = "phase_changed"
    COST_UPDATE = "cost_update"
    HYPOTHESIS_APPROVAL_REQUESTED = "hypothesis_approval_requested"
    DOMAIN_DETECTED = "domain_detected"
    LITERATURE_SURVEY_COMPLETED = "literature_survey_completed"
    VALIDATION_METRICS = "validation_metrics"
    VISUALIZATION = "visualization"


@dataclass(frozen=True)
class SSEEvent:
    event: SSEEventType
    data: dict[str, Any]

    def format(self) -> str:
        return json.dumps({"event": self.event.value, "data": self.data})


def domain_event_to_sse(event: DomainEvent) -> SSEEvent | None:
    if isinstance(event, HypothesisFormulated):
        return SSEEvent(
            event=SSEEventType.HYPOTHESIS_FORMULATED,
            data={
                "hypothesis_id": event.hypothesis_id,
                "statement": event.statement,
                "rationale": event.rationale,
                "prediction": event.prediction,
                "null_prediction": event.null_prediction,
                "success_criteria": event.success_criteria,
                "failure_criteria": event.failure_criteria,
                "scope": event.scope,
                "hypothesis_type": event.hypothesis_type,
                "prior_confidence": event.prior_confidence,
                "parent_id": event.parent_id,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, ExperimentStarted):
        return SSEEvent(
            event=SSEEventType.EXPERIMENT_STARTED,
            data={
                "experiment_id": event.experiment_id,
                "hypothesis_id": event.hypothesis_id,
                "description": event.description,
                "independent_variable": event.independent_variable,
                "dependent_variable": event.dependent_variable,
                "controls": event.controls,
                "analysis_plan": event.analysis_plan,
                "success_criteria": event.success_criteria,
                "failure_criteria": event.failure_criteria,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, ExperimentCompleted):
        return SSEEvent(
            event=SSEEventType.EXPERIMENT_COMPLETED,
            data={
                "experiment_id": event.experiment_id,
                "hypothesis_id": event.hypothesis_id,
                "tool_count": event.tool_count,
                "finding_count": event.finding_count,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, HypothesisEvaluated):
        return SSEEvent(
            event=SSEEventType.HYPOTHESIS_EVALUATED,
            data={
                "hypothesis_id": event.hypothesis_id,
                "status": event.status,
                "confidence": event.confidence,
                "reasoning": event.reasoning,
                "certainty_of_evidence": event.certainty_of_evidence,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, NegativeControlRecorded):
        return SSEEvent(
            event=SSEEventType.NEGATIVE_CONTROL,
            data={
                "identifier": event.identifier,
                "identifier_type": event.identifier_type,
                "name": event.name,
                "score": event.score,
                "threshold": event.threshold,
                "correctly_classified": event.correctly_classified,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, PositiveControlRecorded):
        return SSEEvent(
            event=SSEEventType.POSITIVE_CONTROL,
            data={
                "identifier": event.identifier,
                "identifier_type": event.identifier_type,
                "name": event.name,
                "known_activity": event.known_activity,
                "score": event.score,
                "correctly_classified": event.correctly_classified,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, ToolCalled):
        return SSEEvent(
            event=SSEEventType.TOOL_CALLED,
            data={
                "tool_name": event.tool_name,
                "tool_input": event.tool_input,
                "experiment_id": event.experiment_id,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, ToolResultEvent):
        return SSEEvent(
            event=SSEEventType.TOOL_RESULT,
            data={
                "tool_name": event.tool_name,
                "result_preview": event.result_preview,
                "experiment_id": event.experiment_id,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, FindingRecorded):
        return SSEEvent(
            event=SSEEventType.FINDING_RECORDED,
            data={
                "title": event.title,
                "detail": event.detail,
                "hypothesis_id": event.hypothesis_id,
                "evidence_type": event.evidence_type,
                "evidence": event.evidence,
                "source_type": event.source_type,
                "source_id": event.source_id,
                "evidence_level": event.evidence_level,
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
                "candidates": event.candidates,
                "findings": event.findings,
                "hypotheses": event.hypotheses,
                "negative_controls": event.negative_controls,
                "positive_controls": event.positive_controls,
                "validation_metrics": event.validation_metrics,
                "diagram_url": event.diagram_url,
            },
        )
    if isinstance(event, OutputSummarized):
        return SSEEvent(
            event=SSEEventType.OUTPUT_SUMMARIZED,
            data={
                "tool_name": event.tool_name,
                "original_length": event.original_length,
                "summarized_length": event.summarized_length,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, PhaseChanged):
        return SSEEvent(
            event=SSEEventType.PHASE_CHANGED,
            data={
                "phase": event.phase,
                "name": event.name,
                "description": event.description,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, HypothesisApprovalRequested):
        return SSEEvent(
            event=SSEEventType.HYPOTHESIS_APPROVAL_REQUESTED,
            data={
                "hypotheses": event.hypotheses,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, DomainDetected):
        return SSEEvent(
            event=SSEEventType.DOMAIN_DETECTED,
            data={
                "domain": event.domain,
                "display_config": event.display_config,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, LiteratureSurveyCompleted):
        return SSEEvent(
            event=SSEEventType.LITERATURE_SURVEY_COMPLETED,
            data={
                "pico": event.pico,
                "search_queries": event.search_queries,
                "total_results": event.total_results,
                "included_results": event.included_results,
                "evidence_grade": event.evidence_grade,
                "assessment": event.assessment,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, ValidationMetricsComputed):
        return SSEEvent(
            event=SSEEventType.VALIDATION_METRICS,
            data={
                "z_prime": event.z_prime,
                "z_prime_quality": event.z_prime_quality,
                "positive_control_count": event.positive_control_count,
                "negative_control_count": event.negative_control_count,
                "positive_mean": event.positive_mean,
                "negative_mean": event.negative_mean,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, VisualizationRendered):
        return SSEEvent(
            event=SSEEventType.VISUALIZATION,
            data={
                "viz_type": event.viz_type,
                "title": event.title,
                "data": event.data,
                "config": event.config,
                "domain": event.domain,
                "experiment_id": event.experiment_id,
                "investigation_id": event.investigation_id,
            },
        )
    if isinstance(event, CostUpdate):
        return SSEEvent(
            event=SSEEventType.COST_UPDATE,
            data={
                "input_tokens": event.input_tokens,
                "output_tokens": event.output_tokens,
                "total_tokens": event.total_tokens,
                "total_cost_usd": event.total_cost_usd,
                "tool_calls": event.tool_calls,
                "investigation_id": event.investigation_id,
            },
        )
    return None
