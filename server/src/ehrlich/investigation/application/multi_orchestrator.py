from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from ehrlich.investigation.application.cost_tracker import CostTracker
from ehrlich.investigation.application.prompts import (
    DIRECTOR_EVALUATION_PROMPT,
    DIRECTOR_EXPERIMENT_PROMPT,
    DIRECTOR_FORMULATION_PROMPT,
    DIRECTOR_SYNTHESIS_PROMPT,
    RESEARCHER_EXPERIMENT_PROMPT,
    SUMMARIZER_PROMPT,
)
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
    OutputSummarized,
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


class MultiModelOrchestrator:
    def __init__(
        self,
        director: AnthropicClientAdapter,
        researcher: AnthropicClientAdapter,
        summarizer: AnthropicClientAdapter,
        registry: ToolRegistry,
        max_iterations_per_experiment: int = 10,
        max_hypotheses: int = 6,
        summarizer_threshold: int = 2000,
    ) -> None:
        self._director = director
        self._researcher = researcher
        self._summarizer = summarizer
        self._registry = registry
        self._max_iterations_per_experiment = max_iterations_per_experiment
        self._max_hypotheses = max_hypotheses
        self._summarizer_threshold = summarizer_threshold

    async def run(self, investigation: Investigation) -> AsyncGenerator[DomainEvent, None]:
        investigation.status = InvestigationStatus.RUNNING
        cost = CostTracker()

        try:
            # 1. Literature survey by researcher (quick phase)
            literature_summary = ""
            async for event in self._run_literature_survey(investigation, cost):
                yield event
                if isinstance(event, Thinking):
                    literature_summary += event.text + "\n"

            # 2. Director formulates hypotheses
            formulation = await self._director_call(
                cost,
                DIRECTOR_FORMULATION_PROMPT,
                f"Research prompt: {investigation.prompt}\n\n"
                f"Literature survey results:\n{literature_summary[:3000]}\n\n"
                f"Findings so far:\n"
                + "\n".join(f"- {f.title}: {f.detail}" for f in investigation.findings)
                + "\n\nFormulate 2-4 testable hypotheses and identify negative controls.",
            )

            # Create hypothesis entities
            for h_data in formulation.get("hypotheses", []):
                hypothesis = Hypothesis(
                    statement=h_data.get("statement", ""),
                    rationale=h_data.get("rationale", ""),
                )
                investigation.add_hypothesis(hypothesis)
                yield HypothesisFormulated(
                    hypothesis_id=hypothesis.id,
                    statement=hypothesis.statement,
                    rationale=hypothesis.rationale,
                    parent_id="",
                    investigation_id=investigation.id,
                )

            # Store negative control suggestions for later
            neg_control_suggestions = formulation.get("negative_controls", [])

            # 3. Hypothesis loop
            tested = 0
            while tested < self._max_hypotheses:
                proposed = [
                    h for h in investigation.hypotheses if h.status == HypothesisStatus.PROPOSED
                ]
                if not proposed:
                    break

                hypothesis = proposed[0]
                hypothesis.status = HypothesisStatus.TESTING
                investigation.current_hypothesis_id = hypothesis.id
                tested += 1

                # 3a. Director designs experiment
                design = await self._director_call(
                    cost,
                    DIRECTOR_EXPERIMENT_PROMPT,
                    f"Research prompt: {investigation.prompt}\n\n"
                    f"Hypothesis to test: {hypothesis.statement}\n"
                    f"Rationale: {hypothesis.rationale}\n\n"
                    f"Available tools: {', '.join(self._registry.list_tools())}\n\n"
                    f"Design an experiment to test this hypothesis.",
                )

                experiment = Experiment(
                    hypothesis_id=hypothesis.id,
                    description=design.get("description", f"Test: {hypothesis.statement}"),
                    tool_plan=design.get("tool_plan", []),
                )
                experiment.status = ExperimentStatus.RUNNING
                investigation.add_experiment(experiment)
                investigation.current_experiment_id = experiment.id

                yield ExperimentStarted(
                    experiment_id=experiment.id,
                    hypothesis_id=hypothesis.id,
                    description=experiment.description,
                    investigation_id=investigation.id,
                )

                # 3b. Researcher executes experiment
                exp_tool_count = cost.tool_calls
                exp_finding_count = len(investigation.findings)
                async for event in self._run_researcher_experiment(
                    investigation, hypothesis, experiment, cost, design
                ):
                    yield event

                experiment.status = ExperimentStatus.COMPLETED
                yield ExperimentCompleted(
                    experiment_id=experiment.id,
                    hypothesis_id=hypothesis.id,
                    tool_count=cost.tool_calls - exp_tool_count,
                    finding_count=len(investigation.findings) - exp_finding_count,
                    investigation_id=investigation.id,
                )

                # 3c. Director evaluates hypothesis
                findings_for_hypothesis = [
                    f for f in investigation.findings if f.hypothesis_id == hypothesis.id
                ]
                findings_text = "\n".join(
                    f"- [{f.evidence_type}] {f.title}: {f.detail}" for f in findings_for_hypothesis
                )
                evaluation = await self._director_call(
                    cost,
                    DIRECTOR_EVALUATION_PROMPT,
                    f"Hypothesis: {hypothesis.statement}\n"
                    f"Rationale: {hypothesis.rationale}\n\n"
                    f"Experiment: {experiment.description}\n\n"
                    f"Findings:\n{findings_text}\n\n"
                    f"Evaluate this hypothesis.",
                )

                eval_status = evaluation.get("status", "supported")
                eval_confidence = float(evaluation.get("confidence", 0.5))
                status_map = {
                    "supported": HypothesisStatus.SUPPORTED,
                    "refuted": HypothesisStatus.REFUTED,
                    "revised": HypothesisStatus.REVISED,
                }
                hypothesis.status = status_map.get(eval_status, HypothesisStatus.SUPPORTED)
                hypothesis.confidence = max(0.0, min(1.0, eval_confidence))

                yield HypothesisEvaluated(
                    hypothesis_id=hypothesis.id,
                    status=eval_status,
                    confidence=eval_confidence,
                    reasoning=evaluation.get("reasoning", ""),
                    investigation_id=investigation.id,
                )

                # If revised, add new hypothesis to queue
                if eval_status == "revised" and evaluation.get("revision"):
                    revised = Hypothesis(
                        statement=evaluation["revision"],
                        rationale=evaluation.get("reasoning", "Revised from prior evidence"),
                        parent_id=hypothesis.id,
                    )
                    investigation.add_hypothesis(revised)
                    yield HypothesisFormulated(
                        hypothesis_id=revised.id,
                        statement=revised.statement,
                        rationale=revised.rationale,
                        parent_id=hypothesis.id,
                        investigation_id=investigation.id,
                    )

            # 4. Negative controls (from director suggestions)
            for nc_data in neg_control_suggestions:
                smiles = nc_data.get("smiles", "")
                name = nc_data.get("name", "")
                source = nc_data.get("source", "")
                if smiles:
                    control = NegativeControl(
                        smiles=smiles,
                        name=name,
                        prediction_score=0.0,
                        source=source,
                    )
                    investigation.add_negative_control(control)
                    yield NegativeControlRecorded(
                        smiles=smiles,
                        name=name,
                        prediction_score=0.0,
                        correctly_classified=True,
                        investigation_id=investigation.id,
                    )

            # 5. Director synthesizes
            all_findings_text = "\n".join(
                f"- [H:{f.hypothesis_id}|{f.evidence_type}] {f.title}: {f.detail}"
                for f in investigation.findings
            )
            hypothesis_text = "\n".join(
                f"- {h.id}: {h.statement} -> {h.status.value} (confidence: {h.confidence})"
                for h in investigation.hypotheses
            )
            nc_text = "\n".join(
                f"- {nc.name}: score={nc.prediction_score}, correct={nc.correctly_classified}"
                for nc in investigation.negative_controls
            )

            synthesis = await self._director_call(
                cost,
                DIRECTOR_SYNTHESIS_PROMPT,
                f"Original prompt: {investigation.prompt}\n\n"
                f"Hypothesis outcomes:\n{hypothesis_text}\n\n"
                f"All findings:\n{all_findings_text}\n\n"
                f"Negative controls:\n{nc_text or 'None recorded'}\n\n"
                f"Synthesize final report.",
            )

            # Apply synthesis
            investigation.summary = synthesis.get("summary", "")
            raw_candidates = synthesis.get("candidates") or []
            candidates = [
                Candidate(
                    smiles=c.get("smiles", ""),
                    name=c.get("name", ""),
                    notes=c.get("rationale", c.get("notes", "")),
                    rank=c.get("rank", i + 1),
                    prediction_score=float(c.get("prediction_score", 0.0)),
                    docking_score=float(c.get("docking_score", 0.0)),
                    admet_score=float(c.get("admet_score", 0.0)),
                    resistance_risk=c.get("resistance_risk", "unknown"),
                )
                for i, c in enumerate(raw_candidates)
            ]
            citations = synthesis.get("citations") or []
            investigation.set_candidates(candidates, citations)

            investigation.status = InvestigationStatus.COMPLETED
            investigation.cost_data = cost.to_dict()

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
                for c in candidates
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
            yield InvestigationCompleted(
                investigation_id=investigation.id,
                candidate_count=len(candidates),
                summary=investigation.summary,
                cost=cost.to_dict(),
                candidates=candidate_dicts,
                findings=finding_dicts,
                hypotheses=hypothesis_dicts,
                negative_controls=nc_dicts,
            )

        except Exception as e:
            logger.exception("Investigation %s failed", investigation.id)
            investigation.status = InvestigationStatus.FAILED
            investigation.error = str(e)
            investigation.cost_data = cost.to_dict()
            yield InvestigationError(error=str(e), investigation_id=investigation.id)

    async def _director_call(
        self,
        cost: CostTracker,
        system: str,
        user_message: str,
    ) -> dict[str, Any]:
        response = await self._director.create_message(
            system=system,
            messages=[{"role": "user", "content": user_message}],
            tools=[],
        )
        cost.add_usage(response.input_tokens, response.output_tokens, self._director.model)
        text = ""
        for block in response.content:
            if block["type"] == "text":
                text += block["text"]
        return _parse_json(text)

    async def _summarize_output(
        self,
        cost: CostTracker,
        tool_name: str,
        output: str,
        investigation_id: str,
    ) -> tuple[str, OutputSummarized | None]:
        if len(output) <= self._summarizer_threshold:
            return output, None

        response = await self._summarizer.create_message(
            system=SUMMARIZER_PROMPT,
            messages=[
                {"role": "user", "content": f"Tool: {tool_name}\nOutput:\n{output}"},
            ],
            tools=[],
        )
        cost.add_usage(response.input_tokens, response.output_tokens, self._summarizer.model)
        summarized = ""
        for block in response.content:
            if block["type"] == "text":
                summarized += block["text"]

        event = OutputSummarized(
            tool_name=tool_name,
            original_length=len(output),
            summarized_length=len(summarized),
            investigation_id=investigation_id,
        )
        return summarized, event

    async def _run_literature_survey(
        self,
        investigation: Investigation,
        cost: CostTracker,
    ) -> AsyncGenerator[DomainEvent, None]:
        """Quick literature survey before hypothesis formulation."""
        tool_schemas = self._registry.list_schemas()
        lit_tools = {
            "search_literature",
            "get_reference",
            "explore_dataset",
            "analyze_substructures",
            "compute_properties",
            "record_finding",
            "validate_smiles",
        }
        tool_schemas = [t for t in tool_schemas if t["name"] in lit_tools]

        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": (
                    f"Research prompt: {investigation.prompt}\n\n"
                    f"Conduct a brief literature survey. Search for relevant papers, "
                    f"explore available datasets, and record key findings. "
                    f"Use 3-6 tool calls, then stop."
                ),
            },
        ]

        for _iteration in range(self._max_iterations_per_experiment):
            investigation.iteration += 1
            response = await self._researcher.create_message(
                system=RESEARCHER_EXPERIMENT_PROMPT,
                messages=messages,
                tools=tool_schemas,
            )
            cost.add_usage(response.input_tokens, response.output_tokens, self._researcher.model)

            assistant_content: list[dict[str, Any]] = []
            tool_use_blocks: list[dict[str, Any]] = []

            for block in response.content:
                assistant_content.append(block)
                if block["type"] == "text":
                    yield Thinking(text=block["text"], investigation_id=investigation.id)
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

                yield ToolCalled(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    investigation_id=investigation.id,
                )

                result_str = await self._dispatch_tool(tool_name, tool_input, investigation)

                summarized_str, summarize_event = await self._summarize_output(
                    cost, tool_name, result_str, investigation.id
                )
                if summarize_event is not None:
                    yield summarize_event

                content_for_model = summarized_str if summarize_event else result_str
                preview = result_str[:1500] if len(result_str) > 1500 else result_str
                yield ToolResultEvent(
                    tool_name=tool_name,
                    result_preview=preview,
                    investigation_id=investigation.id,
                )

                if tool_name == "record_finding":
                    finding = Finding(
                        title=tool_input.get("title", ""),
                        detail=tool_input.get("detail", ""),
                        evidence=tool_input.get("evidence", ""),
                        hypothesis_id=tool_input.get("hypothesis_id", ""),
                        evidence_type=tool_input.get("evidence_type", "neutral"),
                    )
                    investigation.record_finding(finding)
                    yield FindingRecorded(
                        title=finding.title,
                        detail=finding.detail,
                        hypothesis_id=finding.hypothesis_id,
                        evidence_type=finding.evidence_type,
                        evidence=finding.evidence,
                        investigation_id=investigation.id,
                    )

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": content_for_model,
                    }
                )

            messages.append({"role": "user", "content": tool_results})

    async def _run_researcher_experiment(
        self,
        investigation: Investigation,
        hypothesis: Hypothesis,
        experiment: Experiment,
        cost: CostTracker,
        design: dict[str, Any],
    ) -> AsyncGenerator[DomainEvent, None]:
        tool_schemas = self._registry.list_schemas()
        excluded = {
            "conclude_investigation",
            "propose_hypothesis",
            "design_experiment",
            "evaluate_hypothesis",
        }
        tool_schemas = [t for t in tool_schemas if t["name"] not in excluded]

        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": (
                    f"Research prompt: {investigation.prompt}\n\n"
                    f"Hypothesis being tested: {hypothesis.statement}\n"
                    f"Rationale: {hypothesis.rationale}\n\n"
                    f"Experiment: {experiment.description}\n"
                    f"Planned tools: {', '.join(experiment.tool_plan)}\n"
                    f"Success criteria: {design.get('success_criteria', 'N/A')}\n"
                    f"Failure criteria: {design.get('failure_criteria', 'N/A')}\n\n"
                    f"Execute this experiment. Link all findings to "
                    f"hypothesis_id='{hypothesis.id}'."
                ),
            },
        ]

        for _iteration in range(self._max_iterations_per_experiment):
            investigation.iteration += 1
            response = await self._researcher.create_message(
                system=RESEARCHER_EXPERIMENT_PROMPT,
                messages=messages,
                tools=tool_schemas,
            )
            cost.add_usage(response.input_tokens, response.output_tokens, self._researcher.model)

            assistant_content: list[dict[str, Any]] = []
            tool_use_blocks: list[dict[str, Any]] = []

            for block in response.content:
                assistant_content.append(block)
                if block["type"] == "text":
                    yield Thinking(text=block["text"], investigation_id=investigation.id)
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

                yield ToolCalled(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    investigation_id=investigation.id,
                )

                result_str = await self._dispatch_tool(tool_name, tool_input, investigation)

                summarized_str, summarize_event = await self._summarize_output(
                    cost, tool_name, result_str, investigation.id
                )
                if summarize_event is not None:
                    yield summarize_event

                content_for_model = summarized_str if summarize_event else result_str
                preview = result_str[:1500] if len(result_str) > 1500 else result_str
                yield ToolResultEvent(
                    tool_name=tool_name,
                    result_preview=preview,
                    investigation_id=investigation.id,
                )

                if tool_name == "record_finding":
                    h_id = tool_input.get("hypothesis_id", hypothesis.id)
                    e_type = tool_input.get("evidence_type", "neutral")
                    finding = Finding(
                        title=tool_input.get("title", ""),
                        detail=tool_input.get("detail", ""),
                        evidence=tool_input.get("evidence", ""),
                        hypothesis_id=h_id,
                        evidence_type=e_type,
                    )
                    investigation.record_finding(finding)
                    h = investigation.get_hypothesis(h_id)
                    if h:
                        if e_type == "supporting":
                            h.supporting_evidence.append(finding.title)
                        elif e_type == "contradicting":
                            h.contradicting_evidence.append(finding.title)
                    yield FindingRecorded(
                        title=finding.title,
                        detail=finding.detail,
                        hypothesis_id=h_id,
                        evidence_type=e_type,
                        evidence=finding.evidence,
                        investigation_id=investigation.id,
                    )

                if tool_name == "record_negative_control":
                    control = NegativeControl(
                        smiles=tool_input.get("smiles", ""),
                        name=tool_input.get("name", ""),
                        prediction_score=float(tool_input.get("prediction_score", 0.0)),
                        source=tool_input.get("source", ""),
                    )
                    investigation.add_negative_control(control)
                    yield NegativeControlRecorded(
                        smiles=control.smiles,
                        name=control.name,
                        prediction_score=control.prediction_score,
                        correctly_classified=control.correctly_classified,
                        investigation_id=investigation.id,
                    )

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": content_for_model,
                    }
                )

            messages.append({"role": "user", "content": tool_results})

    async def _dispatch_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        investigation: Investigation,
    ) -> str:
        func = self._registry.get(tool_name)
        if func is None:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        try:
            result = await func(**tool_input)
            return str(result)
        except Exception as e:
            logger.warning("Tool %s failed: %s", tool_name, e)
            return json.dumps({"error": f"Tool {tool_name} failed: {e}"})


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    return {"raw_text": text}
