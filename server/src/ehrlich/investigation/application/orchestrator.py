from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from ehrlich.investigation.application.cost_tracker import CostTracker
from ehrlich.investigation.application.prompts import SCIENTIST_SYSTEM_PROMPT
from ehrlich.investigation.domain.candidate import Candidate
from ehrlich.investigation.domain.events import (
    DomainEvent,
    ExperimentCompleted,
    ExperimentStarted,
    FindingRecorded,
    HypothesisEvaluated,
    HypothesisFormulated,
    InvestigationCompleted,
    InvestigationError,
    NegativeControlRecorded,
    Thinking,
    ToolCalled,
    ToolResultEvent,
)
from ehrlich.investigation.domain.experiment import Experiment, ExperimentStatus
from ehrlich.investigation.domain.finding import Finding
from ehrlich.investigation.domain.hypothesis import Hypothesis, HypothesisStatus
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus
from ehrlich.investigation.domain.negative_control import NegativeControl

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from ehrlich.investigation.application.tool_registry import ToolRegistry
    from ehrlich.investigation.infrastructure.anthropic_client import AnthropicClientAdapter

logger = logging.getLogger(__name__)

_CONTROL_TOOLS = {
    "record_finding",
    "conclude_investigation",
    "propose_hypothesis",
    "design_experiment",
    "evaluate_hypothesis",
    "record_negative_control",
}


class Orchestrator:
    def __init__(
        self,
        client: AnthropicClientAdapter,
        registry: ToolRegistry,
        max_iterations: int = 50,
    ) -> None:
        self._client = client
        self._registry = registry
        self._max_iterations = max_iterations

    async def run(self, investigation: Investigation) -> AsyncGenerator[DomainEvent, None]:
        investigation.status = InvestigationStatus.RUNNING
        cost = CostTracker()
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": investigation.prompt},
        ]
        tool_schemas = self._registry.list_schemas()
        concluded = False
        experiment_tool_count = 0
        experiment_finding_count = 0

        try:
            for iteration in range(self._max_iterations):
                investigation.iteration = iteration + 1

                response = await self._client.create_message(
                    system=SCIENTIST_SYSTEM_PROMPT,
                    messages=messages,
                    tools=tool_schemas,
                )
                cost.add_usage(response.input_tokens, response.output_tokens, self._client.model)

                assistant_content: list[dict[str, Any]] = []
                tool_use_blocks: list[dict[str, Any]] = []

                for block in response.content:
                    assistant_content.append(block)
                    if block["type"] == "text":
                        yield Thinking(
                            text=block["text"],
                            investigation_id=investigation.id,
                        )
                    elif block["type"] == "tool_use":
                        tool_use_blocks.append(block)

                messages.append({"role": "assistant", "content": assistant_content})

                if response.stop_reason == "end_turn" or not tool_use_blocks:
                    break

                tool_results: list[dict[str, Any]] = []
                for tool_block in tool_use_blocks:
                    tool_name = tool_block["name"]
                    tool_input = tool_block["input"]
                    tool_use_id = tool_block["id"]
                    cost.add_tool_call()

                    if tool_name not in _CONTROL_TOOLS:
                        experiment_tool_count += 1

                    yield ToolCalled(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        investigation_id=investigation.id,
                    )

                    result_str, events = await self._dispatch_tool(
                        tool_name, tool_input, investigation
                    )
                    for event in events:
                        if isinstance(event, FindingRecorded):
                            experiment_finding_count += 1
                        yield event

                    preview = result_str[:1500] if len(result_str) > 1500 else result_str
                    yield ToolResultEvent(
                        tool_name=tool_name,
                        result_preview=preview,
                        investigation_id=investigation.id,
                    )

                    if tool_name == "conclude_investigation":
                        if investigation.current_experiment_id:
                            exp = investigation.get_experiment(investigation.current_experiment_id)
                            if exp and exp.status == ExperimentStatus.RUNNING:
                                exp.status = ExperimentStatus.COMPLETED
                                yield ExperimentCompleted(
                                    experiment_id=exp.id,
                                    hypothesis_id=exp.hypothesis_id,
                                    tool_count=experiment_tool_count,
                                    finding_count=experiment_finding_count,
                                    investigation_id=investigation.id,
                                )
                        concluded = True

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result_str,
                        }
                    )

                messages.append({"role": "user", "content": tool_results})

                if concluded:
                    break

            investigation.status = InvestigationStatus.COMPLETED
            investigation.cost_data = cost.to_dict()
            yield self._build_completed_event(investigation, cost)

        except Exception as e:
            logger.exception("Investigation %s failed", investigation.id)
            investigation.status = InvestigationStatus.FAILED
            investigation.error = str(e)
            yield InvestigationError(
                error=str(e),
                investigation_id=investigation.id,
            )

    async def _dispatch_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        investigation: Investigation,
    ) -> tuple[str, list[DomainEvent]]:
        events: list[DomainEvent] = []

        if tool_name == "propose_hypothesis":
            return self._handle_propose_hypothesis(tool_input, investigation, events)

        if tool_name == "design_experiment":
            return self._handle_design_experiment(tool_input, investigation, events)

        if tool_name == "evaluate_hypothesis":
            return self._handle_evaluate_hypothesis(tool_input, investigation, events)

        if tool_name == "record_finding":
            return self._handle_record_finding(tool_input, investigation, events)

        if tool_name == "record_negative_control":
            return self._handle_record_negative_control(tool_input, investigation, events)

        if tool_name == "conclude_investigation":
            return self._handle_conclude(tool_input, investigation), events

        func = self._registry.get(tool_name)
        if func is None:
            return json.dumps({"error": f"Unknown tool: {tool_name}"}), events

        try:
            result = await func(**tool_input)
            return str(result), events
        except Exception as e:
            logger.warning("Tool %s failed: %s", tool_name, e)
            return json.dumps({"error": f"Tool {tool_name} failed: {e}"}), events

    def _handle_propose_hypothesis(
        self,
        tool_input: dict[str, Any],
        investigation: Investigation,
        events: list[DomainEvent],
    ) -> tuple[str, list[DomainEvent]]:
        hypothesis = Hypothesis(
            statement=tool_input.get("statement", ""),
            rationale=tool_input.get("rationale", ""),
            parent_id=tool_input.get("parent_id", ""),
        )
        investigation.add_hypothesis(hypothesis)
        investigation.current_hypothesis_id = hypothesis.id
        events.append(
            HypothesisFormulated(
                hypothesis_id=hypothesis.id,
                statement=hypothesis.statement,
                rationale=hypothesis.rationale,
                parent_id=hypothesis.parent_id,
                investigation_id=investigation.id,
            )
        )
        return json.dumps(
            {
                "status": "proposed",
                "hypothesis_id": hypothesis.id,
                "statement": hypothesis.statement,
            }
        ), events

    def _handle_design_experiment(
        self,
        tool_input: dict[str, Any],
        investigation: Investigation,
        events: list[DomainEvent],
    ) -> tuple[str, list[DomainEvent]]:
        hypothesis_id = tool_input.get("hypothesis_id", "") or investigation.current_hypothesis_id
        experiment = Experiment(
            hypothesis_id=hypothesis_id,
            description=tool_input.get("description", ""),
            tool_plan=tool_input.get("tool_plan") or [],
        )
        experiment.status = ExperimentStatus.RUNNING
        investigation.add_experiment(experiment)
        investigation.current_experiment_id = experiment.id
        events.append(
            ExperimentStarted(
                experiment_id=experiment.id,
                hypothesis_id=experiment.hypothesis_id,
                description=experiment.description,
                investigation_id=investigation.id,
            )
        )
        return json.dumps({"status": "started", "experiment_id": experiment.id}), events

    def _handle_evaluate_hypothesis(
        self,
        tool_input: dict[str, Any],
        investigation: Investigation,
        events: list[DomainEvent],
    ) -> tuple[str, list[DomainEvent]]:
        hypothesis_id = tool_input.get("hypothesis_id", "")
        new_status = tool_input.get("status", "supported")
        confidence = float(tool_input.get("confidence", 0.0))
        reasoning = tool_input.get("reasoning", "")

        hypothesis = investigation.get_hypothesis(hypothesis_id)
        if hypothesis:
            status_map = {
                "supported": HypothesisStatus.SUPPORTED,
                "refuted": HypothesisStatus.REFUTED,
                "revised": HypothesisStatus.REVISED,
            }
            hypothesis.status = status_map.get(new_status, HypothesisStatus.SUPPORTED)
            hypothesis.confidence = max(0.0, min(1.0, confidence))

        events.append(
            HypothesisEvaluated(
                hypothesis_id=hypothesis_id,
                status=new_status,
                confidence=confidence,
                reasoning=reasoning,
                investigation_id=investigation.id,
            )
        )
        return json.dumps(
            {"status": "evaluated", "hypothesis_id": hypothesis_id, "outcome": new_status}
        ), events

    def _handle_record_finding(
        self,
        tool_input: dict[str, Any],
        investigation: Investigation,
        events: list[DomainEvent],
    ) -> tuple[str, list[DomainEvent]]:
        hypothesis_id = tool_input.get("hypothesis_id", investigation.current_hypothesis_id)
        evidence_type = tool_input.get("evidence_type", "neutral")

        finding = Finding(
            title=tool_input.get("title", ""),
            detail=tool_input.get("detail", ""),
            evidence=tool_input.get("evidence", ""),
            hypothesis_id=hypothesis_id,
            evidence_type=evidence_type,
        )
        investigation.record_finding(finding)

        hypothesis = investigation.get_hypothesis(hypothesis_id)
        if hypothesis:
            if evidence_type == "supporting":
                hypothesis.supporting_evidence.append(finding.title)
            elif evidence_type == "contradicting":
                hypothesis.contradicting_evidence.append(finding.title)

        events.append(
            FindingRecorded(
                title=finding.title,
                detail=finding.detail,
                hypothesis_id=hypothesis_id,
                evidence_type=evidence_type,
                evidence=finding.evidence,
                investigation_id=investigation.id,
            )
        )
        return json.dumps(
            {
                "status": "recorded",
                "title": finding.title,
                "hypothesis_id": hypothesis_id,
                "total_findings": len(investigation.findings),
            }
        ), events

    def _handle_record_negative_control(
        self,
        tool_input: dict[str, Any],
        investigation: Investigation,
        events: list[DomainEvent],
    ) -> tuple[str, list[DomainEvent]]:
        control = NegativeControl(
            smiles=tool_input.get("smiles", ""),
            name=tool_input.get("name", ""),
            prediction_score=float(tool_input.get("prediction_score", 0.0)),
            source=tool_input.get("source", ""),
        )
        investigation.add_negative_control(control)
        events.append(
            NegativeControlRecorded(
                smiles=control.smiles,
                name=control.name,
                prediction_score=control.prediction_score,
                correctly_classified=control.correctly_classified,
                investigation_id=investigation.id,
            )
        )
        return json.dumps(
            {
                "status": "recorded",
                "name": control.name,
                "prediction_score": control.prediction_score,
                "correctly_classified": control.correctly_classified,
            }
        ), events

    def _handle_conclude(self, tool_input: dict[str, Any], investigation: Investigation) -> str:
        investigation.summary = tool_input.get("summary", "")
        raw_candidates = tool_input.get("candidates") or []
        candidates = [
            Candidate(
                smiles=c.get("smiles", ""),
                name=c.get("name", ""),
                notes=c.get("rationale", c.get("notes", "")),
                rank=i + 1,
                prediction_score=float(c.get("prediction_score", 0.0)),
                docking_score=float(c.get("docking_score", 0.0)),
                admet_score=float(c.get("admet_score", 0.0)),
                resistance_risk=c.get("resistance_risk", "unknown"),
            )
            for i, c in enumerate(raw_candidates)
        ]
        citations = tool_input.get("citations") or []
        investigation.set_candidates(candidates, citations)
        return json.dumps(
            {
                "status": "concluded",
                "summary": investigation.summary[:200],
                "candidate_count": len(candidates),
                "citation_count": len(citations),
            }
        )

    def _build_completed_event(
        self, investigation: Investigation, cost: CostTracker
    ) -> InvestigationCompleted:
        candidate_dicts = [
            {
                "smiles": c.smiles,
                "name": c.name,
                "rank": c.rank,
                "notes": c.notes,
                "prediction_score": c.prediction_score,
                "docking_score": c.docking_score,
                "admet_score": c.admet_score,
                "resistance_risk": c.resistance_risk,
            }
            for c in investigation.candidates
        ]
        finding_dicts = [
            {
                "title": f.title,
                "detail": f.detail,
                "hypothesis_id": f.hypothesis_id,
                "evidence_type": f.evidence_type,
                "evidence": f.evidence,
            }
            for f in investigation.findings
        ]
        hypothesis_dicts = [
            {
                "id": h.id,
                "statement": h.statement,
                "rationale": h.rationale,
                "status": h.status.value,
                "parent_id": h.parent_id,
                "confidence": h.confidence,
                "supporting_evidence": h.supporting_evidence,
                "contradicting_evidence": h.contradicting_evidence,
            }
            for h in investigation.hypotheses
        ]
        nc_dicts = [
            {
                "smiles": nc.smiles,
                "name": nc.name,
                "prediction_score": nc.prediction_score,
                "correctly_classified": nc.correctly_classified,
                "source": nc.source,
            }
            for nc in investigation.negative_controls
        ]
        return InvestigationCompleted(
            investigation_id=investigation.id,
            candidate_count=len(investigation.candidates),
            summary=investigation.summary,
            cost=cost.to_dict(),
            candidates=candidate_dicts,
            findings=finding_dicts,
            hypotheses=hypothesis_dicts,
            negative_controls=nc_dicts,
        )
