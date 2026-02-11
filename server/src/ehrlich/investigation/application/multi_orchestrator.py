from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from ehrlich.investigation.application.cost_tracker import CostTracker
from ehrlich.investigation.application.prompts import (
    DIRECTOR_PLANNING_PROMPT,
    DIRECTOR_REVIEW_PROMPT,
    DIRECTOR_SYNTHESIS_PROMPT,
    RESEARCHER_PHASE_PROMPT,
    SUMMARIZER_PROMPT,
)
from ehrlich.investigation.domain.candidate import Candidate
from ehrlich.investigation.domain.events import (
    DirectorDecision,
    DirectorPlanning,
    DomainEvent,
    FindingRecorded,
    InvestigationCompleted,
    InvestigationError,
    OutputSummarized,
    PhaseCompleted,
    PhaseStarted,
    Thinking,
    ToolCalled,
    ToolResultEvent,
)
from ehrlich.investigation.domain.finding import Finding
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from ehrlich.investigation.application.tool_registry import ToolRegistry
    from ehrlich.investigation.infrastructure.anthropic_client import AnthropicClientAdapter

logger = logging.getLogger(__name__)

_RESEARCH_PHASES = [
    "Literature Review",
    "Data Exploration",
    "Model Training",
    "Virtual Screening",
    "Structural Analysis",
    "Resistance Assessment",
]

_PHASE_KEYWORDS: dict[str, str] = {
    "literature": "Literature Review",
    "search_literature": "Literature Review",
    "get_reference": "Literature Review",
    "explore_dataset": "Data Exploration",
    "analyze_substructures": "Data Exploration",
    "compute_properties": "Data Exploration",
    "train_model": "Model Training",
    "predict_candidates": "Virtual Screening",
    "cluster_compounds": "Virtual Screening",
    "compute_descriptors": "Structural Analysis",
    "generate_3d": "Structural Analysis",
    "dock_against_target": "Structural Analysis",
    "predict_admet": "Structural Analysis",
    "assess_resistance": "Resistance Assessment",
}


class MultiModelOrchestrator:
    def __init__(
        self,
        director: AnthropicClientAdapter,
        researcher: AnthropicClientAdapter,
        summarizer: AnthropicClientAdapter,
        registry: ToolRegistry,
        max_iterations_per_phase: int = 10,
        summarizer_threshold: int = 2000,
    ) -> None:
        self._director = director
        self._researcher = researcher
        self._summarizer = summarizer
        self._registry = registry
        self._max_iterations_per_phase = max_iterations_per_phase
        self._summarizer_threshold = summarizer_threshold

    async def run(self, investigation: Investigation) -> AsyncGenerator[DomainEvent, None]:
        investigation.status = InvestigationStatus.RUNNING
        cost = CostTracker()

        try:
            # 1. Director plans
            yield DirectorPlanning(stage="planning", phase="", investigation_id=investigation.id)
            plan = await self._director_call(
                cost,
                DIRECTOR_PLANNING_PROMPT,
                f"Research prompt: {investigation.prompt}\n\nCreate a research plan.",
            )
            yield DirectorDecision(
                stage="planning", decision=plan, investigation_id=investigation.id
            )

            phases = _RESEARCH_PHASES
            if "phases" in plan:
                custom_names = [p.get("name", "") for p in plan.get("phases", []) if p.get("name")]
                if custom_names:
                    phases = custom_names

            # 2. Execute each phase with Researcher
            all_phase_summaries: list[str] = []
            for phase_name in phases:
                investigation.start_phase(phase_name)
                yield PhaseStarted(phase=phase_name, investigation_id=investigation.id)

                phase_summary = ""
                phase_tool_count = cost.tool_calls
                phase_finding_count = len(investigation.findings)
                async for event in self._run_researcher_phase(
                    investigation, phase_name, cost, plan
                ):
                    yield event
                    if isinstance(event, Thinking):
                        phase_summary += event.text + "\n"

                yield PhaseCompleted(
                    phase=phase_name,
                    tool_count=cost.tool_calls - phase_tool_count,
                    finding_count=len(investigation.findings) - phase_finding_count,
                    investigation_id=investigation.id,
                )

                # Director reviews phase
                yield DirectorPlanning(
                    stage="review", phase=phase_name, investigation_id=investigation.id
                )
                findings_text = "\n".join(
                    f"- {f.title}: {f.detail}" for f in investigation.findings
                )
                review = await self._director_call(
                    cost,
                    DIRECTOR_REVIEW_PROMPT,
                    f"Phase: {phase_name}\n\nPhase activity:\n{phase_summary[:3000]}\n\n"
                    f"Findings so far:\n{findings_text}\n\nAssess quality and decide.",
                )
                yield DirectorDecision(
                    stage="review", decision=review, investigation_id=investigation.id
                )
                all_phase_summaries.append(f"## {phase_name}\n{phase_summary[:1000]}")

                if not review.get("proceed", True):
                    break

            # 3. Director synthesizes
            yield DirectorPlanning(stage="synthesis", phase="", investigation_id=investigation.id)
            findings_text = "\n".join(
                f"- [{f.phase}] {f.title}: {f.detail}" for f in investigation.findings
            )
            synthesis = await self._director_call(
                cost,
                DIRECTOR_SYNTHESIS_PROMPT,
                f"Original prompt: {investigation.prompt}\n\n"
                f"Phase summaries:\n{''.join(all_phase_summaries)}\n\n"
                f"All findings:\n{findings_text}\n\nSynthesize final report.",
            )
            yield DirectorDecision(
                stage="synthesis", decision=synthesis, investigation_id=investigation.id
            )

            # 4. Apply synthesis to investigation
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
                    "phase": f.phase,
                    "evidence": f.evidence,
                }
                for f in investigation.findings
            ]
            yield InvestigationCompleted(
                investigation_id=investigation.id,
                candidate_count=len(candidates),
                summary=investigation.summary,
                cost=cost.to_dict(),
                candidates=candidate_dicts,
                findings=finding_dicts,
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

    async def _run_researcher_phase(
        self,
        investigation: Investigation,
        phase_name: str,
        cost: CostTracker,
        plan: dict[str, Any],
    ) -> AsyncGenerator[DomainEvent, None]:
        phase_guidance = ""
        for p in plan.get("phases", []):
            if p.get("name") == phase_name:
                goals = ", ".join(p.get("goals", []))
                questions = ", ".join(p.get("key_questions", []))
                phase_guidance = f"Goals: {goals}\nKey questions: {questions}"
                break

        tool_schemas = self._registry.list_schemas()
        # Filter out conclude_investigation for the researcher
        tool_schemas = [t for t in tool_schemas if t["name"] != "conclude_investigation"]

        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": (
                    f"Research prompt: {investigation.prompt}\n\n"
                    f"Current phase: {phase_name}\n{phase_guidance}\n\n"
                    f"Execute this phase thoroughly."
                ),
            },
        ]

        for _iteration in range(self._max_iterations_per_phase):
            investigation.iteration += 1
            response = await self._researcher.create_message(
                system=RESEARCHER_PHASE_PROMPT,
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

                phase = _PHASE_KEYWORDS.get(tool_name)
                if phase and phase != investigation.current_phase:
                    investigation.start_phase(phase)
                    yield PhaseStarted(phase=phase, investigation_id=investigation.id)

                yield ToolCalled(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    investigation_id=investigation.id,
                )

                result_str = await self._dispatch_tool(tool_name, tool_input, investigation)

                # Summarize large outputs
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
                    yield FindingRecorded(
                        title=tool_input.get("title", ""),
                        detail=tool_input.get("detail", ""),
                        phase=tool_input.get("phase", investigation.current_phase),
                        evidence=tool_input.get("evidence", ""),
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
        if tool_name == "record_finding":
            finding = Finding(
                title=tool_input.get("title", ""),
                detail=tool_input.get("detail", ""),
                evidence=tool_input.get("evidence", ""),
                phase=tool_input.get("phase", investigation.current_phase),
            )
            investigation.record_finding(finding)
            return json.dumps(
                {
                    "status": "recorded",
                    "title": finding.title,
                    "phase": finding.phase,
                    "total_findings": len(investigation.findings),
                }
            )

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
